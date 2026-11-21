import csv
from io import StringIO
from calendar import Calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, abort, current_app, flash, redirect, render_template, request, session, url_for
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash

from dados_demo import MESES
from database.gestao import perfil

admin = Blueprint("gestao", __name__, url_prefix="/admin/gestao")
PAGES = ("visao", "inicio", "notas", "calendario", "comunicados", "perfil", "configuracoes",
         "usuarios", "administradores", "turmas", "professores")


@admin.before_request
def authorize():
    if request.environ["unifica.account"]["papel"] != "administrador":
        abort(403)


def value(key, limit, optional=False):
    result = request.form.get(key, "").strip()
    if len(result) > limit or (not optional and not result):
        raise ValueError("Confira o campo " + key + ".")
    return result


def choice(key, options):
    result = request.form.get(key)
    if result not in options:
        raise ValueError("Seleção inválida: " + key + ".")
    return result


def account_change(cur, key, delete):
    f = request.form
    actor = request.environ["unifica.account"]["matricula"]
    if key:
        cur.execute("SELECT papel, nome, matricula FROM unifica_contas WHERE matricula=%s FOR UPDATE", (key,))
        old = cur.fetchone()
        if not old:
            abort(404)
        key = old[2]
        if key in (actor, "admin") and (delete or f.get("ativo") == "0"):
            raise ValueError("Esta conta administrativa precisa permanecer ativa.")
        if delete:
            cur.execute("DELETE FROM unifica_sessoes WHERE matricula=%s", (key,))
            cur.execute("DELETE FROM unifica_contas WHERE matricula=%s", (key,))
            return old[1]
    nome, email = value("nome", 150), value("email", 254)
    if "@" not in email:
        raise ValueError("Confira o e-mail.")
    role = old[0] if key else choice("papel", ("aluno", "administrador", "professor"))
    turma = value("turma", 80, optional=role != "aluno")
    if turma:
        cur.execute("INSERT IGNORE INTO unifica_turmas(nome) VALUES (%s)", (turma,))
    active = choice("ativo", ("0", "1"))
    if key:
        cur.execute("UPDATE unifica_contas SET nome=%s,email=%s,turma=%s WHERE matricula=%s",
                    (nome, email, turma, key))
    else:
        key = value("matricula", 60).lower()
        pw = f.get("senha", "")
        if not 8 <= len(pw) <= 256:
            raise ValueError("Use uma senha de 8 a 256 caracteres.")
        cur.execute("""INSERT INTO unifica_contas(matricula,nome,email,turma,papel,senha)
                       VALUES (%s,%s,%s,%s,%s,%s)""", (key,nome,email,turma,role,generate_password_hash(pw)))
    cur.execute("""INSERT INTO unifica_perfis(matricula,ativo) VALUES(%s,%s)
                   ON DUPLICATE KEY UPDATE ativo=%s""", (key, active, active))
    if active == "0":
        cur.execute("DELETE FROM unifica_sessoes WHERE matricula=%s", (key,))
    return nome


def academic_change(cur, kind, key, delete):
    # Only table and column names from these fixed definitions enter SQL.
    schemas = {
        "turma": ("unifica_turmas", ("nome",)),
        "evento": ("unifica_eventos", ("titulo","dia","inicio","fim","descricao")),
        "comunicado": ("unifica_comunicados", ("titulo","conteudo","publicacao","status","categoria")),
        "nota": ("unifica_notas", ("matricula","disciplina","periodo","nota","aulas","faltas")),
    }
    if kind not in schemas:
        abort(404)
    table, fields = schemas[kind]
    if key:
        cur.execute(f"SELECT {fields[0]} FROM {table} WHERE id=%s FOR UPDATE", (key,))
        old = cur.fetchone()
        if not old:
            abort(404)
    if delete:
        if kind == "turma":
            cur.execute("SELECT 1 FROM unifica_contas WHERE turma=%s LIMIT 1", old)
            if cur.fetchone():
                raise ValueError("Transfira os usuários desta turma antes de excluí-la.")
        cur.execute(f"DELETE FROM {table} WHERE id=%s", (key,))
        return str(old[0])
    if kind == "turma":
        vals = [value("nome",80)]
        if key:
            cur.execute("UPDATE unifica_contas SET turma=%s WHERE turma=%s", (vals[0],old[0]))
    elif kind == "evento":
        vals = [value("titulo",150), date.fromisoformat(value("dia",10)),
                datetime.strptime(value("inicio",5),"%H:%M").time(),
                datetime.strptime(value("fim",5),"%H:%M").time(), value("descricao",4000,True)]
        if vals[3] <= vals[2]:
            raise ValueError("O término precisa ser posterior ao início.")
    elif kind == "comunicado":
        vals = [value("titulo",150),value("conteudo",8000),datetime.fromisoformat(value("publicacao",16)),
                choice("status",("Publicado","Rascunho")),choice("categoria",("avisos","prazos","calendario"))]
    else:
        ra = value("matricula",60)
        cur.execute("SELECT papel FROM unifica_contas WHERE matricula=%s FOR UPDATE", (ra,))
        if cur.fetchone() != ("aluno",):
            raise ValueError("Selecione um aluno cadastrado.")
        nota = Decimal(value("nota",5))
        periodo, aulas, faltas = (int(value(k,5)) for k in ("periodo","aulas","faltas"))
        if not (nota.is_finite() and 0 <= nota <= 10 and 1 <= periodo <= 4 and 0 <= faltas <= aulas and aulas > 0):
            raise ValueError("Confira nota, período, aulas e faltas.")
        vals = [ra,value("disciplina",100),periodo,nota,aulas,faltas]
    if key:
        assignments = ",".join(f"{field}=%s" for field in fields)
        cur.execute(f"UPDATE {table} SET {assignments} WHERE id=%s", (*vals,key))
    else:
        placeholders = ",".join(["%s"] * len(fields))
        cur.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({placeholders})", vals)
    return str(vals[0])


@admin.post("/alterar/<kind>")
def change(kind):
    store = current_app.extensions["store"]
    ra = request.environ["unifica.account"]["matricula"]
    page = choice("pagina", PAGES)
    key = value("id",60,True)
    delete = request.form.get("acao") == "excluir"
    if delete and not key:
        abort(400)
    try:
        with store.connection() as conn:
            with conn.cursor() as cur:
                if kind in ("perfil","preferencias"):
                    cur.execute("INSERT IGNORE INTO unifica_perfis(matricula) VALUES(%s)", (ra,))
                    if kind == "perfil":
                        nome,email = value("nome",150),value("email",254)
                        cur.execute("UPDATE unifica_contas SET nome=%s,email=%s WHERE matricula=%s",(nome,email,ra))
                        cur.execute("""UPDATE unifica_perfis SET cargo=%s,escola=%s,departamento=%s,telefone=%s
                                       WHERE matricula=%s""", (*[value(k,n,True) for k,n in
                                       (("cargo",100),("escola",150),("departamento",100),("telefone",40))],ra))
                    else:
                        tema = choice("tema",("claro","escuro"))
                        fonte = choice("fonte",("normal","grande"))
                        cur.execute("UPDATE unifica_perfis SET tema=%s,fonte=%s WHERE matricula=%s",(tema,fonte,ra))
                    label = kind.capitalize()
                elif kind == "conta":
                    label = account_change(cur,key,delete)
                else:
                    label = academic_change(cur,kind,key,delete)
                verb = "Exclusão" if delete else "Atualização" if key or kind in ("perfil","preferencias") else "Cadastro"
                cur.execute("""INSERT INTO unifica_atividade(momento,acao,tipo,matricula)
                               VALUES(NOW(),%s,'gestao',%s)""",(f"{verb} · {kind} · {label}"[:200],ra))
        flash("Exclusão concluída." if delete else "Alterações salvas com sucesso.", "sucesso")
    except IntegrityError:
        flash("Registro duplicado ou vinculado a outro cadastro. Confira os dados.", "erro")
    except (ValueError, InvalidOperation) as exc:
        flash(str(exc) if isinstance(exc, ValueError) else "Valor numérico inválido.", "erro")
    params = {}
    if page == "calendario":
        params["dia"] = request.form.get("dia") or request.form.get("dia_atual","")
    return redirect(url_for("gestao.screen", page=page, **params),303)


@admin.get("/<page>")
def screen(page):
    if page not in PAGES:
        abort(404)
    store = current_app.extensions["store"]
    def rows(sql, args=()):
        return store.query(sql,args,rows=True)
    today = date.today()
    try:
        day = date.fromisoformat(request.args.get("dia",""))
        if not 1900 <= day.year <= 2100:
            day = today
    except ValueError:
        day = today
    first = day.replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)
    accounts = rows("""SELECT c.matricula,c.nome,c.email,c.turma,c.papel,COALESCE(p.ativo,1) ativo
                        FROM unifica_contas c LEFT JOIN unifica_perfis p USING(matricula) ORDER BY c.nome""")
    events = rows("""SELECT id,titulo,DATE_FORMAT(dia,'%Y-%m-%d') dia,TIME_FORMAT(inicio,'%H:%i') inicio,
                          TIME_FORMAT(fim,'%H:%i') fim,descricao FROM unifica_eventos ORDER BY dia,inicio""")
    notices = rows("""SELECT id,titulo,conteudo,DATE_FORMAT(publicacao,'%Y-%m-%dT%H:%i') publicacao,
                          status,categoria FROM unifica_comunicados ORDER BY publicacao DESC,id DESC""")
    grades = rows("""SELECT n.*,c.nome,c.turma FROM unifica_notas n JOIN unifica_contas c USING(matricula)
                     ORDER BY c.nome,n.periodo,n.disciplina""")
    groups = rows("SELECT id,nome FROM unifica_turmas ORDER BY nome")
    stats = rows("""SELECT DATE(momento) dia,COUNT(*) acessos,COUNT(DISTINCT IF(tipo='aluno',matricula,NULL)) alunos
                    FROM unifica_atividade WHERE tipo IN ('aluno','professor','administrador')
                    AND momento >= CURRENT_DATE - INTERVAL 6 DAY GROUP BY DATE(momento)""")
    index = {r["dia"]:r for r in stats}
    series=[]
    for i in range(7):
        d=today-timedelta(days=6-i)
        series.append(dict(dia=d.strftime("%d/%m"), **{k:index.get(d,{}).get(k,0) for k in ("acessos","alunos")}))
    personal = perfil(store,request.environ["unifica.account"]["matricula"])
    return render_template("gestao.html",page=page,accounts=accounts,groups=groups,events=events,
        notices=notices,grades=grades,personal=personal,series=series,
        actions=rows("SELECT acao,momento FROM unifica_atividade WHERE tipo='gestao' ORDER BY id DESC LIMIT 6"),
        today=today.isoformat(),now=datetime.now().strftime("%Y-%m-%dT%H:%M"),day=day,
        month=MESES[day.month-1],weeks=Calendar(6).monthdatescalendar(day.year,day.month),
        previous=first-timedelta(days=1),following=next_month)


@admin.get("/relatorios/notas.csv")
def report():
    store = current_app.extensions["store"]
    registros = store.query("""SELECT c.matricula,c.nome,c.turma,n.disciplina,n.periodo,n.nota,n.aulas,n.faltas
        FROM unifica_notas n JOIN unifica_contas c USING(matricula) ORDER BY c.nome,n.periodo,n.disciplina""", rows=True)
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    fields = ("matricula","nome","turma","disciplina","periodo","nota","aulas","faltas")
    writer.writerow(("Matrícula","Nome","Turma","Disciplina","Bimestre","Nota","Aulas","Faltas"))
    for r in registros:
        cells = [str(r[k]) for k in fields]
        writer.writerow(["'" + cell if cell.lstrip().startswith(("=", "+", "-", "@")) else cell for cell in cells])
    return Response("\ufeff"+output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=notas-frequencia.csv"})
