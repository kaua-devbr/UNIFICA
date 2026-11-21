import secrets
import time
from datetime import timedelta
from urllib.parse import urlsplit
from flask import abort, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from auth.gateway import digest
from database.gestao import perfil


def destination(value):
    parts = urlsplit(value)
    if parts.path in {"/", "/inicio", "/perfil", "/calendario", "/comunicados", "/notas",
                      "/admin/alunos", "/configuracoes", "/biblioteca", "/biblioteca/"} and not (parts.netloc or parts.scheme):
        return parts.path + ("?" + parts.query if parts.query else "")
    return "/"


def configure_identity(app, store):
    app.permanent_session_lifetime = timedelta(days=7)

    @app.before_request
    def protect_form():
        session.setdefault("csrf", secrets.token_urlsafe())
        if request.method == "POST" and session["csrf"] != request.form.get("csrf"):
            abort(400)

    def revoke():
        token = session.get("token")
        if token:
            store.query("DELETE FROM unifica_sessoes WHERE token=?", (digest(token),))
        session.clear()

    @app.route("/sso/login", methods=["GET", "POST"])
    def login():
        dest = destination(request.values.get("destino", "/"))
        error = None
        if request.method == "POST":
            account = store.account(request.form.get("matricula", "").strip().lower())
            if account and perfil(store, account["matricula"]).get("ativo",1) and check_password_hash(account["senha"], request.form.get("senha", "")):
                revoke()
                token = secrets.token_urlsafe(32)
                remember = bool(request.form.get("lembrar"))
                now = int(time.time())
                store.query("DELETE FROM unifica_sessoes WHERE expira<=?", (now,))
                store.query("INSERT INTO unifica_sessoes (token,matricula,expira) VALUES (?,?,?)",
                            (digest(token), account["matricula"], now + (604800 if remember else 28800)))
                store.query("""INSERT INTO unifica_atividade(momento,acao,tipo,matricula)
                               VALUES(NOW(),'Login',?,?)""",(account["papel"],account["matricula"]))
                session.update(token=token, csrf=secrets.token_urlsafe())
                session.permanent = remember
                return redirect(dest, 303)
            error = "Matrícula ou senha incorreta."
        return render_template("identidade.html", titulo="Entrar no UNIFICA", modo="login", erro=error, destino=dest)

    @app.route("/sso/sair", methods=["GET", "POST"])
    def sair():
        if request.method == "POST":
            revoke()
            return redirect("/sso/login", 303)
        return render_template("identidade.html", titulo="Sair de todos os serviços?", modo="sair")

    @app.route("/sso/senha", methods=["GET", "POST"])
    def senha():
        token = session.get("token", "")
        rows = store.query("""SELECT c.* FROM unifica_contas c JOIN unifica_sessoes s
            ON c.matricula=s.matricula WHERE s.token=? AND s.expira>?""",
            (digest(token), int(time.time())), rows=True)
        if not rows:
            return redirect("/sso/login")
        error = None
        if request.method == "POST":
            account = rows[0]
            new = request.form.get("nova", "")
            if check_password_hash(account["senha"], request.form.get("atual", "")) and 8 <= len(new) <= 256:
                with store.connection() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE unifica_contas SET senha=%s WHERE matricula=%s AND senha=%s",
                                (generate_password_hash(new), account["matricula"], account["senha"]))
                    if cur.rowcount != 1:
                        abort(409)
                    cur.execute("""INSERT INTO unifica_perfis(matricula,senha_em) VALUES (%s,NOW())
                                   ON DUPLICATE KEY UPDATE senha_em=NOW()""",(account["matricula"],))
                    cur.execute("DELETE FROM unifica_sessoes WHERE matricula=%s", (account["matricula"],))
                session.clear()
                return redirect("/sso/login", 303)
            error = "Confira a senha atual e use de 8 a 256 caracteres na nova."
        return render_template("identidade.html", titulo="Alterar senha", modo="senha", erro=error)

