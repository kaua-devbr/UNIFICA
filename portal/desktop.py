"""Interface do Flet. O gateway valida a mesma sessão usada pelo portal."""
from datetime import date, timedelta

from flask import Blueprint, abort, current_app, request, session
from mysql.connector import IntegrityError

from database.gestao import perfil
from portal.gestao import academic_change, account_change, authorize, change, screen

api = Blueprint("desktop", __name__, url_prefix="/desktop/api")


def store():
    return current_app.extensions["store"]


def conta():
    return request.environ["unifica.account"]


def registros_notas(banco, matricula):
    return banco.query("""SELECT disciplina,periodo,nota,aulas,faltas FROM unifica_notas
                          WHERE matricula=? ORDER BY periodo,disciplina""", (matricula,), rows=True)


def publicados(banco):
    return banco.query("""SELECT id,categoria,titulo,conteudo,publicacao FROM unifica_comunicados
        WHERE status='Publicado' AND publicacao<=NOW() ORDER BY publicacao DESC,id DESC""", rows=True)


def agenda(banco, primeiro, seguinte):
    return banco.query("""SELECT id,dia,titulo,descricao,TIME_FORMAT(inicio,'%H:%i') inicio,
        TIME_FORMAT(fim,'%H:%i') fim FROM unifica_eventos
        WHERE dia>=? AND dia<? ORDER BY dia,inicio,id""", (primeiro,seguinte), rows=True)


def preferencias(banco, ra, tema, fonte):
    if tema not in ("claro","escuro") or fonte not in ("pequena","normal","grande"):
        raise ValueError("Preferências inválidas.")
    banco.query("""INSERT INTO unifica_perfis(matricula,tema,fonte) VALUES(?,?,?)
        ON DUPLICATE KEY UPDATE tema=?,fonte=?""", (ra,tema,fonte,tema,fonte))


@api.get("/conta")
def dados_conta():
    p = perfil(store(), conta()["matricula"])
    return dict(conta(), tema=p.get("tema","claro"), fonte=p.get("fonte","normal"),
                escola=p.get("escola",""), form_token=session["form_token"])


@api.get("/notas")
def notas():
    return {"itens": registros_notas(store(), conta()["matricula"])}


@api.get("/comunicados")
def comunicados():
    return {"itens": [dict(r,publicacao=r["publicacao"].isoformat()) for r in publicados(store())]}


@api.get("/eventos")
def eventos():
    try:
        primeiro = date(int(request.args["ano"]),int(request.args["mes"]),1)
        seguinte = (primeiro + timedelta(days=32)).replace(day=1)
    except (ValueError,OverflowError):
        abort(400)
    return {"itens": [dict(r,dia=r["dia"].isoformat()) for r in agenda(store(),primeiro,seguinte)]}


@api.post("/perfil")
def editar_perfil():
    nome,email,escola = (request.form.get(k,"").strip() for k in ("nome","email","escola"))
    if not (0 < len(nome) <= 150 and "@" in email and len(email)<=254 and len(escola)<=150):
        return {"erro":"Confira o nome, o e-mail e a escola."},400
    ra = conta()["matricula"]
    with store().connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE unifica_contas SET nome=%s,email=%s WHERE matricula=%s",(nome,email,ra))
        cur.execute("""INSERT INTO unifica_perfis(matricula,escola) VALUES(%s,%s)
                       ON DUPLICATE KEY UPDATE escola=%s""",(ra,escola,escola))
    return {"ok":True}


@api.post("/preferencias")
def salvar_estilo():
    try:
        preferencias(store(),conta()["matricula"],request.form.get("tema"),request.form.get("fonte"))
    except ValueError as err:
        return {"erro":str(err)},400
    return {"ok":True}


@api.post("/admin/<tipo>")
def cadastrar(tipo):
    authorize()
    if tipo not in ("aluno","evento"):
        abort(404)
    if tipo=="aluno" and request.form.get("papel")!="aluno":
        abort(400)
    try:
        with store().connection() as conn, conn.cursor() as cur:
            if tipo=="aluno":
                label = account_change(cur,"",False)
            else:
                label = academic_change(cur,"evento","",False)
            cur.execute("""INSERT INTO unifica_atividade(momento,acao,tipo,matricula)
                        VALUES(NOW(),%s,'gestao',%s)""",(f"Cadastro · {tipo} · {label}"[:200],conta()["matricula"]))
    except IntegrityError:
        return {"erro":"Registro duplicado ou inválido."},409
    except ValueError as err:
        return {"erro":str(err)},400
    return {"ok":True},201



@api.get("/gestao")
def painel_admin():
    authorize()
    return screen("visao", desktop=True)


@api.post("/gestao/<kind>")
def modificar_admin(kind):
    authorize()
    return change(kind, desktop=True)
