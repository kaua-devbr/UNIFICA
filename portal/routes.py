from calendar import Calendar
from datetime import date, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from auth.decorators import login_required
from portal.boletim import DISCIPLINAS_DEMO, AULAS_DEMO

portal = Blueprint("portal", __name__)

MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
)
DIAS = ("Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo")
EVENTOS = {
    date(2026, 11, 6): [
        ("09:00–10:00", "Reunião de Alinhamento Semanal"),
        ("14:30–16:00", "Apresentação do Projeto"),
    ],
    date(2026, 11, 9): [("10:00", "Atividade de Geografia")],
    date(2026, 11, 12): [("14:00", "Entrega de PNT Desktop")],
    date(2026, 11, 16): [("09:00", "Reunião de turma")],
    date(2026, 11, 20): [("10:00", "Aulão para o Enem")],
    date(2026, 11, 25): [("13:00", "Apresentações da turma")],
    date(2026, 11, 30): [("09:00", "Encerramento do mês")],
}
CATEGORIAS = {
    "todos": "Todos",
    "prazos": "Prazos e Entregas",
    "avisos": "Avisos Importantes",
    "calendario": "Calendário",
}
COMUNICADOS = [
    (1, "calendario", "Calendário Acadêmico", "Confira as novas datas do calendário acadêmico.", "Há 2 dias"),
    (2, "prazos", "Atividade Pendente", "Entrega do trabalho de Geografia até sexta-feira.", "Há 3 dias"),
    (3, "avisos", "Aviso Importante", "Mudança na sala de aula de Programação.", "Há 1 semana"),
    (4, "prazos", "Atividade Pendente", "Entrega do trabalho de PNT Desktop até amanhã.", "Há 2 semanas"),
    (5, "avisos", "Aviso Importante", "Aulão para o Enem na próxima quinta-feira.", "Há 3 semanas"),
]


@portal.get("/")
def login():
    return redirect(url_for("portal.inicio"))


@portal.get("/healthz")
def health():
    # Sonda local: nao inicia login nem cria uma sessao OIDC.
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
        selecionado = date.fromisoformat(request.args.get("dia", "2026-11-06"))
        if not 1900 <= selecionado.year <= 2100:
            raise ValueError
    except ValueError:
        selecionado = date(2026, 11, 6)

    primeiro = selecionado.replace(day=1)
    anterior = (primeiro - timedelta(days=1)).replace(day=1)
    seguinte = (primeiro + timedelta(days=32)).replace(day=1)
    return render_template(
        "calendario.html",
        selecionado=selecionado,
        titulo_mes=f"{MESES[selecionado.month - 1].capitalize()} de {selecionado.year}",
        titulo_dia=f"{DIAS[selecionado.weekday()]}, {selecionado.day:02d} de {MESES[selecionado.month - 1]}",
        semanas=Calendar(firstweekday=6).monthdatescalendar(selecionado.year, selecionado.month),
        anterior=anterior if anterior.year >= 1900 else None,
        seguinte=seguinte if seguinte.year <= 2100 else None,
        eventos=EVENTOS,
    )


@portal.route("/comunicados", methods=["GET", "POST"])
@login_required
def comunicados():
    categoria = request.args.get("categoria", "todos")
    if categoria not in CATEGORIAS:
        categoria = "todos"
    busca = request.args.get("busca", "").strip()[:100]
    if request.method == "POST":
        lidos = set(session.get("comunicados_lidos", []))
        comunicado = request.form.get("comunicado")
        lidos.update(item[0] for item in COMUNICADOS if comunicado in ("todos", str(item[0])))
        session["comunicados_lidos"] = sorted(lidos)
        return redirect(url_for("portal.comunicados", categoria=categoria, busca=busca), code=303)

    resultados = [
        item for item in COMUNICADOS
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
    from flask import current_app
    current_app.extensions["store"].query("DELETE FROM unifica_sessoes WHERE token=?",
                                          (request.environ["unifica.session"],))
    session.clear()
    return redirect("/sso/login", 303)



@portal.app_errorhandler(404)
@portal.app_errorhandler(500)
def erro_portal(erro):
    return render_template("erro.html", codigo=erro.code), erro.code
