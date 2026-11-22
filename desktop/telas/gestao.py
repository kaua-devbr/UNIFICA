from calendar import Calendar
from datetime import date, datetime, timedelta
from pathlib import Path
import flet as ft

from cliente import ErroPortal, SessaoExpirada
from .comum import botao, campo, cartao, titulo

MENU = [("Visão geral", "/visao"), ("Alunos", "/inicio"), ("Notas e frequência", "/notas"),
        ("Calendário", "/calendario"), ("Comunicados", "/comunicados"),
        ("Perfil", "/perfil"), ("Configurações", "/configuracoes")]
LISTAS = {
    "inicio": ("Alunos", "aluno", "accounts"), "usuarios": ("Usuários", "conta", "accounts"),
    "administradores": ("Administradores", "administrador", "accounts"),
    "professores": ("Professores", "professor", "accounts"), "turmas": ("Turmas", "turma", "groups"),
    "comunicados": ("Comunicados", "comunicado", "notices"), "notas": ("Notas e frequência", "nota", "grades"),
}
TIPOS = {"conta":"usuário", "aluno":"aluno", "administrador":"administrador", "professor":"professor",
         "turma":"turma", "nota":"registro acadêmico", "evento":"evento", "comunicado":"comunicado", "perfil":"perfil"}


def selecao(label, pares, valor=None):
    opcoes = [ft.DropdownOption(key=str(k), text=t) for k,t in pares]
    return ft.Dropdown(label=label, options=opcoes, value=valor, editable=False)


def construir(page, ctx, rota):
    secao = rota.strip("/")
    api = ctx["crud"].api
    dados = api("gestao")
    usuario = ctx["usuario"]
    alunos = [a for a in dados["accounts"] if a["papel"] == "aluno"]
    hoje = date.today()
    dia = date.fromisoformat(ctx.get("dia_admin", hoje.isoformat()))
    itens = []

    def ir(destino):
        ctx["mostrar"]("/" + destino)

    def link(texto, destino):
        return ft.TextButton(texto, on_click=lambda e: ir(destino))

    def info(texto):
        page.show_dialog(ft.AlertDialog(title=ft.Text(texto), actions=[
            ft.TextButton("OK", on_click=lambda e: page.pop_dialog())]))

    def formulario(tipo, registro=None, excluir=False):
        registro = registro or {}
        conta = tipo in ("conta","aluno","professor","administrador")
        recurso = "conta" if conta else tipo
        chave = registro.get("matricula" if conta else "id", "")
        campos = {}
        controles = []
        erro = ft.Text(color="#D14A45")
        def adicionar(k, label, opcoes=None, padrao="", secreto=False, longo=False):
            valor = str(registro.get(k, padrao) or "") if registro.get(k, padrao) != 0 else "0"
            item = selecao(label, opcoes, valor) if opcoes is not None else campo(label, secreto, valor)
            if longo:
                item.multiline = True
                item.min_lines = 3
            campos[k] = item
            controles.append(item)
            return item

        def seletor(k, label, valor, horario=False):
            formato = "%H:%M" if horario else "%Y-%m-%d"
            inicial = datetime.strptime(valor, formato)
            valores_selecionados[k] = valor
            def atualizar(e):
                escolhido = e.control.value
                valores_selecionados[k] = escolhido.strftime(formato)
                botao_data.content = label + " · " + escolhido.strftime("%H:%M" if horario else "%d/%m/%Y")
                page.update()
            def abrir(e):
                atual = datetime.strptime(valores_selecionados[k], formato)
                if horario:
                    popup = ft.TimePicker(value=atual.time(),entry_mode=ft.TimePickerEntryMode.DIAL_ONLY,on_change=atualizar)
                else:
                    popup = ft.DatePicker(value=atual,first_date=datetime(1000,1,1),last_date=datetime(9999,12,31),
                                          entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,on_change=atualizar)
                page.show_dialog(popup)
            botao_data = ft.OutlinedButton(label+" · "+inicial.strftime("%H:%M" if horario else "%d/%m/%Y"),on_click=abrir)
            controles.append(botao_data)
        valores_selecionados = {}

        if excluir:
            nome = registro.get("nome") or registro.get("titulo") or registro.get("disciplina")
            controles.append(ft.Text(f'Excluir {TIPOS[tipo]} “{nome}”? Essa ação é permanente.'))
        elif conta:
            if not chave:
                adicionar("matricula","Matrícula")
                if tipo == "conta":
                    adicionar("papel","Tipo de usuário",[(r,r.capitalize()) for r in ("aluno","professor","administrador")],"aluno")
            adicionar("nome","Nome completo")
            adicionar("email","E-mail")
            nomes = sorted({g["nome"] for g in dados["groups"]} | {a["turma"] for a in dados["accounts"] if a["turma"]})
            nova = campo("Nome da nova turma")
            atual = registro.get("turma") or ""
            # Index keys allow even a class whose name matches a UI label.
            opcoes = [("", "Sem turma")] + [(str(i),n) for i,n in enumerate(nomes)] + [("nova","Digitar nova turma…")]
            turma = selecao("Turma", opcoes, str(nomes.index(atual)) if atual else ("nova" if not nomes else ""))
            nova.visible = turma.value == "nova"
            def escolher(e):
                nova.visible = turma.value == "nova"
                page.update()
            turma.on_select = escolher
            controles.extend([turma,nova])
            materia = adicionar("materia","Matéria lecionada")
            def ajustar_papel(e=None):
                papel = registro.get("papel") or (campos["papel"].value if tipo=="conta" else tipo)
                materia.visible = papel=="professor"
                turma.visible = not materia.visible
                nova.visible = turma.visible and turma.value=="nova"
                if e is not None:
                    page.update()
            if "papel" in campos:
                campos["papel"].on_select = ajustar_papel
            ajustar_papel()
            adicionar("ativo","Situação",[("1","Ativo"),("0","Inativo")],"1")
            if not chave:
                adicionar("senha","Senha inicial",secreto=True)
        elif tipo == "turma":
            adicionar("nome","Nome da turma")
        elif tipo == "nota":
            if not alunos:
                info("Cadastre um aluno para registrar notas e frequência.")
                return
            adicionar("matricula","Aluno",[(a["matricula"],a["nome"]+" · "+a["matricula"]) for a in alunos], alunos[0]["matricula"])
            adicionar("disciplina","Disciplina")
            adicionar("periodo","Bimestre",[(str(i),f"{i}º bimestre") for i in range(1,5)],"1")
            for k,label in [("nota","Nota (0 a 10)"),("aulas","Aulas"),("faltas","Faltas")]:
                adicionar(k,label,padrao="0" if k=="faltas" else "")
        elif tipo == "evento":
            adicionar("titulo","Título")
            seletor("dia","Data",registro.get("dia",dia.isoformat()))
            seletor("inicio","Início",registro.get("inicio","09:00"),True)
            seletor("fim","Término",registro.get("fim","10:00"),True)
            adicionar("descricao","Descrição",longo=True)
        elif tipo == "comunicado":
            adicionar("titulo","Título")
            adicionar("conteudo","Conteúdo da publicação",longo=True)
            publicacao = registro.get("publicacao",datetime.now().isoformat(timespec="minutes"))
            seletor("data_publicacao","Data da publicação",publicacao[:10])
            seletor("hora_publicacao","Hora da publicação",publicacao[11:16],True)
            adicionar("categoria","Categoria",[("avisos","Avisos"),("prazos","Prazos"),("calendario","Calendário")],"avisos")
            adicionar("status","Status",[(s,s) for s in ("Publicado","Rascunho")],"Publicado")
        elif tipo == "perfil":
            for k,label in PERFIL:
                adicionar(k,label)

        def enviar(e):
            valores = {k:item.value for k,item in campos.items()}
            valores.update(valores_selecionados)
            if tipo=="comunicado" and not excluir:
                valores["publicacao"] = valores.pop("data_publicacao")+"T"+valores.pop("hora_publicacao")
            if conta and not excluir:
                if not materia.visible:
                    valores.pop("materia",None)
                valores["turma"] = nova.value.strip() if turma.value=="nova" else nomes[int(turma.value)] if turma.value else ""
                if not chave and tipo!="conta":
                    valores["papel"] = tipo
            if tipo=="nota" and not excluir:
                valores["nota"] = valores["nota"].replace(",",".")
            try:
                api("gestao/"+recurso, dict(valores, pagina=secao, id=str(chave), acao="excluir" if excluir else "salvar"))
            except SessaoExpirada as exc:
                page.pop_dialog()
                ctx["mostrar_login"]()
                ctx["aviso"](str(exc))
                return
            except ErroPortal as exc:
                erro.value = str(exc)
                page.update()
                return
            page.pop_dialog()
            if tipo=="evento" and not excluir:
                ctx["dia_admin"] = valores["dia"]
            ir(secao)
            info("Exclusão concluída." if excluir else "Alterações salvas com sucesso.")
        verbo = "Excluir" if excluir else "Editar" if registro else "Cadastrar"
        page.show_dialog(ft.AlertDialog(modal=True, title=titulo(f"{verbo} {TIPOS[tipo]}",20),
            content=ft.Container(width=510,content=ft.Column([*controles,erro],tight=True,scroll=ft.ScrollMode.AUTO)),
            actions=[ft.TextButton("Cancelar",on_click=lambda e:page.pop_dialog()),botao("Excluir" if excluir else "Salvar",enviar)]))

    def novo(label,tipo):
        return botao(label,lambda e:formulario(tipo))

    def linha(tipo,r,texto):
        return ft.Row([ft.Text(texto,expand=True),
            ft.TextButton("Editar",on_click=lambda e:formulario(tipo,r)),
            ft.TextButton("Excluir",on_click=lambda e:formulario(tipo,r,True))])

    def bloco(label, linhas):
        return cartao(ft.Column([titulo(label,18), *linhas]))

    if secao in ("visao","inicio"):
        itens.append(titulo("Olá, Administrador!" if secao=="visao" else "Gestão de alunos"))
        pendentes = sum(n["status"]=="Rascunho" for n in dados["notices"])
        indicadores = [(len(alunos),"Alunos","inicio"),(len(dados["groups"]),"Turmas","turmas"),
                       (pendentes,"Comunicados pendentes","comunicados"),(len(dados["notices"]),"Comunicados","comunicados")]
        itens.append(ft.Row([link(f"{n} · {label}",dest) for n,label,dest in indicadores],wrap=True))
        itens.append(bloco("Ações rápidas",[ft.Row([novo("Cadastrar aluno","aluno"),novo("Registrar nota","nota"),
            novo("Criar evento","evento"),novo("Publicar comunicado","comunicado")],wrap=True),
            ft.Row([link(LISTAS[k][0],k) for k in ("usuarios","administradores","turmas","professores")],wrap=True)]))
    if secao=="visao":
        pico = max([1] + [r["acessos"] for r in dados["series"]])
        serie = [ft.Column([ft.Text(f"{r['dia']} · {r['acessos']} acessos · {r['alunos']} alunos ativos"),
                            ft.ProgressBar(value=r["acessos"]/pico, color="#5146D8"),
                            ft.ProgressBar(value=r["alunos"]/pico, color="#159B70")]) for r in dados["series"]]
        itens.append(bloco("Estatísticas dos últimos sete dias",serie))
        eventos = [r for r in dados["events"] if r["dia"]>=hoje.isoformat()][:4]
        def abrir_evento(data):
            ctx["dia_admin"] = data
            ir("calendario")
        itens.append(bloco("Próximos eventos",[ft.TextButton(r["dia"]+" · "+r["titulo"],
            on_click=lambda e,d=r["dia"]:abrir_evento(d)) for r in eventos] or [ft.Text("Nenhum evento agendado.")]))
        itens.append(bloco("Comunicados recentes",[link(r["titulo"],"comunicados") for r in dados["notices"][:4]] or [ft.Text("Nenhum comunicado.")]))
    elif secao in LISTAS:
        label,tipo,tabela = LISTAS[secao]
        registros = dados[tabela]
        if tipo in ("aluno","administrador","professor"):
            registros = [r for r in registros if r["papel"]==tipo]
        itens.extend([titulo(label),novo("Cadastrar "+TIPOS[tipo],tipo)])
        busca = campo("Pesquisar por nome, matrícula, título ou conteúdo")
        filtros = {}
        if tipo=="nota":
            for k,label in (("turma","Turma"),("disciplina","Disciplina"),("periodo","Bimestre")):
                valores = sorted({str(r[k]) for r in registros})
                filtros[k] = selecao(label,[("","Todos")]+[(v,v) for v in valores],"")
        if tipo=="comunicado":
            filtros["status"] = selecao("Status",[("","Todos"),("Publicado","Publicado"),("Rascunho","Rascunho")],"")
        lista = ft.Column()
        pagina = 0
        frequencia = False
        def preencher():
            nonlocal pagina
            encontrados = [r for r in registros if busca.value.casefold() in " ".join(map(str,r.values())).casefold()
                          and all(not c.value or str(r[k])==c.value for k,c in filtros.items())]
            total = max(1,(len(encontrados)+5)//6)
            pagina = min(pagina,total-1)
            linhas = []
            for r in encontrados[pagina*6:pagina*6+6]:
                if tabela=="accounts":
                    texto = f"{r['nome']} · {r['matricula']} · {(r.get('materia') or 'Matéria não informada') if r['papel']=='professor' else r['turma']} · " + ("Ativo" if r["ativo"] else "Inativo")
                elif tipo=="nota":
                    detalhe = f"Nota {r['nota']}"
                    if frequencia:
                        presenca = 100*(r["aulas"]-r["faltas"])/r["aulas"] if r["aulas"] else 0
                        detalhe = f"{presenca:.1f}% de presença · {r['faltas']} faltas em {r['aulas']} aulas"
                    texto = f"{r['nome']} · {r['disciplina']} · {r['periodo']}º bim. · {detalhe}"
                elif tipo=="comunicado":
                    texto = f"{r['titulo']} · {r['status']} · {r['publicacao']}\n{r['conteudo']}"
                else:
                    texto = r["nome"]
                linhas.append(linha(tipo,r,texto))
            def mover(delta):
                nonlocal pagina
                pagina += delta
                preencher()
                page.update()
            lista.controls = (linhas or [ft.Text("Nenhum registro encontrado.")])+[ft.Row([
                ft.TextButton("Anterior",disabled=pagina==0,on_click=lambda e:mover(-1)),
                ft.Text(f"{pagina+1} / {total}"),ft.TextButton("Próxima",disabled=pagina+1>=total,on_click=lambda e:mover(1))])]
        def filtrar(e):
            nonlocal pagina
            pagina = 0
            preencher()
            page.update()
        busca.on_change = filtrar
        for c in filtros.values():
            c.on_select = filtrar
        preencher()
        itens.extend([busca,*filtros.values()])
        if tipo=="nota":
            modo = selecao("Exibir",[("notas","Notas"),("frequencia","Frequência")],"notas")
            def alternar(e):
                nonlocal frequencia
                frequencia = modo.value == "frequencia"
                filtrar(e)
            modo.on_select = alternar
            itens.append(modo)
        itens.append(lista)
        if secao=="inicio":
            itens.append(bloco("Últimas ações",[ft.Text(r["acao"]) for r in dados["actions"]] or [ft.Text("Nenhuma ação registrada.")]))
    elif secao=="calendario":
        def selecionar(d):
            ctx["dia_admin"] = d.isoformat()
            ir("calendario")
        primeiro = dia.replace(day=1)
        proximo = (primeiro+timedelta(days=32)).replace(day=1)
        datas = {r["dia"] for r in dados["events"]}
        itens.extend([titulo("Calendário"),novo("Novo evento","evento"),ft.Row([
            ft.TextButton("Mês anterior",on_click=lambda e:selecionar(primeiro-timedelta(days=1))),
            titulo(dia.strftime("%m / %Y"),18), ft.TextButton("Próximo mês",on_click=lambda e:selecionar(proximo))])])
        itens.append(ft.Row([ft.Text(d,expand=True) for d in ("Dom","Seg","Ter","Qua","Qui","Sex","Sáb")]))
        for semana in Calendar(6).monthdatescalendar(dia.year,dia.month):
            itens.append(ft.Row([ft.Button(str(d.day)+(" •" if d.isoformat() in datas else ""),expand=True,
                bgcolor="#5146D8" if d==dia else None, color="white" if d==dia else None,
                disabled=d.month!=dia.month,on_click=lambda e,d=d:selecionar(d)) for d in semana]))
        itens.append(bloco("Eventos de "+dia.strftime("%d/%m/%Y"),[linha("evento",r,r["inicio"]+"–"+r["fim"]+" · "+r["titulo"]) for r in dados["events"] if r["dia"]==dia.isoformat()] or [ft.Text("Nenhum evento neste dia.")]))
    elif secao=="perfil":
        perfil = dict(dados["personal"],nome=usuario["nome"],email=usuario["email"])
        itens.extend([titulo("Perfil de administrador"),bloco(usuario["nome"],[ft.Text(label+" · "+str(perfil.get(k) or "—")) for k,label in PERFIL]),
            botao("Editar perfil",lambda e:formulario("perfil",perfil))])
    if secao in ("notas","perfil"):
        async def exportar(e):
            try:
                r = ctx["crud"].requisitar("GET","/admin/gestao/relatorios/notas.csv")
                if r.status_code!=200 or "text/csv" not in r.headers.get("content-type",""):
                    raise ErroPortal("Não foi possível obter o relatório. Confira sua sessão.")
                nome = await ft.FilePicker().save_file(file_name="notas-frequencia.csv")
                if nome:
                    Path(nome).write_bytes(r.content)
                    ctx["aviso"]("Relatório salvo.")
            except (OSError,ErroPortal) as exc:
                ctx["aviso"](str(exc))
        itens.append(ft.TextButton("Exportar relatório de notas e frequência",on_click=exportar))
    return ft.Column(itens,scroll=ft.ScrollMode.AUTO,spacing=14)


PERFIL = [("nome","Nome completo"),("email","E-mail institucional"),("cargo","Cargo"),
          ("escola","Escola"),("departamento","Departamento"),("telefone","Telefone")]
