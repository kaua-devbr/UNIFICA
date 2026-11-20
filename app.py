from pathlib import Path
import os
import secrets
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor"))

from flask import Flask, abort, redirect, render_template, request, session
from auth.gateway import Gateway
from auth.identity import configure_identity
from database.store import Store
from portal.routes import portal


def create_app(folder=None):
    folder = Path(folder or ROOT / "instance")
    folder.mkdir(parents=True, exist_ok=True)
    store = Store(folder)
    store.initialize()
    if not store.account("admin"):
        password = secrets.token_urlsafe(15)
        store.create("admin", "Administração", "", "", "administrador", password)
        print(f"Primeiro acesso | matrícula: admin | senha: {password}", flush=True)

    keyfile = folder / "secret.key"
    if not keyfile.exists():
        with keyfile.open("xb") as file:
            file.write(secrets.token_bytes(48))
    import hmac
    key = keyfile.read_bytes()
    def service(name):
        app = Flask(name, root_path=str(ROOT))
        app.config.update(SECRET_KEY=hmac.digest(key, name.encode(), "sha256"),
                          SESSION_COOKIE_NAME="unifica_" + name, SESSION_COOKIE_SAMESITE="Lax",
                          TRUSTED_HOSTS=["127.0.0.1", "localhost"])
        return app

    identity = service("identidade")
    configure_identity(identity, store)
    web = service("portal_aluno")
    web.register_blueprint(portal)
    web.extensions["store"] = store

    @web.before_request
    def load_account():
        account = request.environ.get("unifica.account")
        if not account:
            return
        sid = request.environ["unifica.session"]
        if session.get("sid") != sid:
            session.clear()
            session.update(sid=sid, usuario=account["nome"], nivel=account["papel"],
                           form_token=secrets.token_urlsafe())
        if request.method == "POST" and request.form.get("form_token") != session["form_token"]:
            abort(400)

    @web.route("/admin/alunos", methods=["GET", "POST"])
    def alunos():
        if request.environ["unifica.account"]["papel"] != "administrador":
            abort(403)
        error = None
        if request.method == "POST":
            fields = [request.form.get(k, "").strip() for k in ("matricula", "nome", "email", "turma")]
            fields[0] = fields[0].lower()
            password = request.form.get("senha", "")
            if not all(0 < len(x) <= limit for x, limit in zip(fields, (60,150,254,80))) or not 8 <= len(password) <= 256:
                error = "Preencha os campos e escolha uma senha de 8 a 256 caracteres."
            elif store.account(fields[0]):
                error = "Essa matrícula já está cadastrada."
            else:
                try:
                    store.create(*fields, "aluno", password)
                except Exception:
                    if not store.account(fields[0]):
                        raise
                    error = "Essa matrícula já está cadastrada."
                else:
                    return redirect("/admin/alunos?cadastrado=1", 303)
        students = store.query("SELECT nome,matricula,turma FROM unifica_contas WHERE papel=? ORDER BY nome", ("aluno",), rows=True)
        return render_template("alunos.html", alunos=students, erro=error)

    library = service("biblioteca")
    @library.get("/")
    def biblioteca():
        return render_template("biblioteca.html", conta=request.environ["unifica.account"])

    gateway = Gateway(identity, web.wsgi_app, library, store)
    web.wsgi_app = gateway
    return web


if __name__ == "__main__":
    from waitress import serve
    app = create_app()
    print("UNIFICA disponível em http://127.0.0.1:5000 | Ctrl+C encerra.", flush=True)
    serve(app, host="127.0.0.1", port=5000)

