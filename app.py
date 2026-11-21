from pathlib import Path
from calendar import Calendar
from datetime import date, timedelta
import hmac
import secrets
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor"))

from flask import (Blueprint, Flask, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from auth.gateway import Gateway
from auth.identity import configure_identity
from database.store import Store
import database.crud as crud
from database import gestao as academic
from portal.gestao import admin
from auth.decorators import login_required
from dados_demo import AULAS_DEMO, CATEGORIAS, DIAS, DISCIPLINAS_DEMO, MESES


portal = Blueprint("portal", __name__)


@portal.get("/")
def login():
    return redirect(url_for("portal.inicio"))


@portal.get("/healthz")
def health():
    return {"status": "ok"}


@portal.get("/perfil")
@login_required
def perfil():
    return render_template("perfil.html", nome=session["usuario"], nivel=session["nivel"])


@portal.get("/inicio")
@login_required
def inicio():
    return render_template("dashboard.html")


@portal.get("/notas")
@login_required
def notas():
    registros = current_app.extensions["store"].query(
        "SELECT disciplina,periodo,nota,aulas,faltas FROM unifica_notas WHERE matricula=? ORDER BY periodo,disciplina",
        (request.environ["unifica.account"]["matricula"],), rows=True)
    if registros:
        aulas = sum(r["aulas"] for r in registros)
        faltas = sum(r["faltas"] for r in registros)
        return render_template("notas.html", reais=True, aulas=aulas, faltas=faltas,
            disciplinas=[(f"{r['disciplina']} · {r['periodo']}º bimestre",r["nota"],r["faltas"]) for r in registros],
            media=sum(r["nota"] for r in registros)/len(registros), frequencia=100*(aulas-faltas)/aulas)
    notas_lancadas = [nota for _, nota, _ in DISCIPLINAS_DEMO if nota is not None]
    faltas = sum(faltas for _, _, faltas in DISCIPLINAS_DEMO)
    return render_template(
        "notas.html",
        disciplinas=DISCIPLINAS_DEMO,
        media=sum(notas_lancadas) / len(notas_lancadas),
        frequencia=100 * (AULAS_DEMO - faltas) / AULAS_DEMO,
        faltas=faltas,
        aulas=AULAS_DEMO,
    )


@portal.get("/calendario")
@login_required
def calendario():
    try:
        selecionado = date.fromisoformat(request.args.get("dia", date.today().isoformat()))
        if not 1900 <= selecionado.year <= 2100:
            raise ValueError
    except ValueError:
        selecionado = date.today()

    primeiro = selecionado.replace(day=1)
    anterior = (primeiro - timedelta(days=1)).replace(day=1)
    seguinte = (primeiro + timedelta(days=32)).replace(day=1)
    eventos = {}
    for r in current_app.extensions["store"].query(
            """SELECT dia,titulo,TIME_FORMAT(inicio,'%H:%i') inicio,TIME_FORMAT(fim,'%H:%i') fim
               FROM unifica_eventos WHERE dia>=? AND dia<? ORDER BY dia,inicio""",(primeiro,seguinte),rows=True):
        eventos.setdefault(r["dia"],[]).append((f"{r['inicio']}–{r['fim']}",r["titulo"]))
    return render_template(
        "calendario.html",
        selecionado=selecionado,
        titulo_mes=f"{MESES[selecionado.month - 1].capitalize()} de {selecionado.year}",
        titulo_dia=f"{DIAS[selecionado.weekday()]}, {selecionado.day:02d} de {MESES[selecionado.month - 1]}",
        semanas=Calendar(firstweekday=6).monthdatescalendar(selecionado.year, selecionado.month),
        anterior=anterior if anterior.year >= 1900 else None,
        seguinte=seguinte if seguinte.year <= 2100 else None,
        eventos=eventos,
    )


@portal.route("/comunicados", methods=["GET", "POST"])
@login_required
def comunicados():
    publicados = current_app.extensions["store"].query(
        """SELECT id,categoria,titulo,conteudo,publicacao FROM unifica_comunicados
           WHERE status='Publicado' AND publicacao<=NOW() ORDER BY publicacao DESC,id DESC""", rows=True)
    comunicados = [(r["id"],r["categoria"],r["titulo"],r["conteudo"],r["publicacao"].strftime("%d/%m/%Y %H:%M"))
                   for r in publicados]
    categoria = request.args.get("categoria", "todos")
    if categoria not in CATEGORIAS:
        categoria = "todos"
    busca = request.args.get("busca", "").strip()[:100]
    if request.method == "POST":
        lidos = set(session.get("comunicados_lidos", []))
        comunicado = request.form.get("comunicado")
        lidos.update(item[0] for item in comunicados if comunicado in ("todos", str(item[0])))
        session["comunicados_lidos"] = sorted(lidos)
        return redirect(url_for("portal.comunicados", categoria=categoria, busca=busca), code=303)

    resultados = [
        item for item in comunicados
        if (categoria == "todos" or item[1] == categoria)
        and busca.casefold() in f"{item[2]} {item[3]}".casefold()
    ]
    return render_template(
        "comunicados.html", comunicados=resultados, categorias=CATEGORIAS,
        categoria=categoria, busca=busca, lidos=session.get("comunicados_lidos", []),
    )


@portal.route("/configuracoes", methods=["GET", "POST"])
@login_required
def configuracoes():
    if request.method == "POST":
        if request.form.get("acao") == "aparencia":
            tema = request.form.get("tema")
            fonte = request.form.get("fonte")
            if tema in ("claro", "escuro") and fonte in ("normal", "grande"):
                session["tema"] = tema
                session["fonte"] = fonte
                flash("Preferências salvas.", "sucesso")
        elif request.form.get("acao") == "senha":
            return redirect("/sso/senha", code=303)
        return redirect(url_for("portal.configuracoes"), code=303)

    return render_template("configuracoes.html")


@portal.post("/sair")
@login_required
def sair():
    current_app.extensions["store"].query("DELETE FROM unifica_sessoes WHERE token=?",
                                          (request.environ["unifica.session"],))
    session.clear()
    return redirect("/sso/login", 303)



@portal.app_errorhandler(404)
@portal.app_errorhandler(500)
def erro_portal(erro):
    return render_template("erro.html", codigo=erro.code), erro.code


def so_administrador():
    if request.environ["unifica.account"]["papel"] != "administrador":
        abort(403)


@portal.route("/admin/alunos", methods=["GET", "POST"])
def alunos():
    so_administrador()
    store = current_app.extensions["store"]
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
                crud.cadastrar_aluno(*fields, password)
            except Exception:
                if not store.account(fields[0]):
                    raise
                error = "Essa matrícula já está cadastrada."
            else:
                return redirect("/admin/alunos?cadastrado=1", 303)
    return render_template("alunos.html", alunos=crud.listar_alunos(), erro=error)


@portal.route("/admin/alunos/<matricula>/editar", methods=["GET", "POST"])
def editar_aluno(matricula):
    so_administrador()
    aluno = crud.buscar_aluno(matricula)
    if aluno is None:
        abort(404)
    error = None
    if request.method == "POST":
        nome, email, turma = [request.form.get(k, "").strip() for k in ("nome", "email", "turma")]
        if not all(0 < len(x) <= limit for x, limit in zip((nome, email, turma), (150, 254, 80))):
            error = "Preencha todos os campos."
            aluno = (matricula, nome, email, turma)
        else:
            crud.atualizar_aluno(matricula, nome, email, turma)
            return redirect("/admin/alunos?editado=1", 303)
    return render_template("aluno_editar.html", aluno=aluno, erro=error)


@portal.post("/admin/alunos/<matricula>/excluir")
def excluir_aluno(matricula):
    so_administrador()
    crud.deletar_aluno(matricula)
    return redirect("/admin/alunos?excluido=1", 303)


def create_app(folder=None):
    folder = Path(folder or ROOT / "instance")
    folder.mkdir(parents=True, exist_ok=True)
    store = Store()
    store.initialize()
    academic.initialize(store)
    if not store.account("admin"):
        password = secrets.token_urlsafe(15)
        store.create("admin", "Administração", "", "", "administrador", password)
        print(f"Primeiro acesso | matrícula: admin | senha: {password}", flush=True)

    keyfile = folder / "secret.key"
    if not keyfile.exists():
        with keyfile.open("xb") as file:
            file.write(secrets.token_bytes(48))
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
    web.register_blueprint(admin)
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
        if account["papel"] == "administrador" and request.method == "GET":
            pages = {"portal.inicio":"visao", "portal.perfil":"perfil", "portal.notas":"notas",
                     "portal.calendario":"calendario", "portal.comunicados":"comunicados",
                     "portal.configuracoes":"configuracoes"}
            if request.endpoint in pages:
                return redirect(url_for("gestao.screen", page=pages[request.endpoint]))

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

