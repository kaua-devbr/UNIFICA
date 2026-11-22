import flet as ft
from .comum import *

def construir(page, ctx):
    usuario = ctx["usuario"]
    crud = ctx["crud"]
    notas = crud.api("notas")["itens"]
    aulas = sum(r["aulas"] for r in notas)
    frequencia = 100 * (aulas - sum(r["faltas"] for r in notas)) / aulas if aulas else None
    media = sum(float(r["nota"]) for r in notas)/len(notas) if notas else None
    media_texto = f"{media:.1f}" if media is not None else "—"
    freq_texto = f"{frequencia:.1f}%" if frequencia is not None else "—"
    comunicados = crud.api("comunicados")["itens"][:3]
    indicadores = ft.Row([
        cartao(ft.Column([ft.Text("Média Geral", color=AZUL),
                          titulo(media_texto, 27)]), expand=True),
        cartao(ft.Column([ft.Text("Frequência", color=AZUL),
                          titulo(freq_texto, 27)]), expand=True),
        cartao(ft.Column([ft.Text("Turma", color=AZUL),
                          titulo(usuario.get("turma") or "Não informada", 23)]), expand=True)
    ], spacing=15)

    proximas = cartao(ft.Column([
        titulo("Minha Próxima Aula", 18),
        ft.Text("Consulte o calendário para acompanhar seus eventos.")
    ]), expand=True)

    linhas_notas = [ft.Row([
        ft.Text("Disciplina", weight=ft.FontWeight.BOLD, expand=True),
        ft.Text("Nota", weight=ft.FontWeight.BOLD, width=60)
    ])]
    for n in notas[:5]:
        linhas_notas.append(ft.Row([
            ft.Text(f"{n['disciplina']} · {n['periodo']}º bim.", expand=True),
            ft.Text(str(n["nota"]), width=60)
        ]))
    bloco_notas = cartao(ft.Column([titulo("Notas Recentes", 18), *linhas_notas]),
                         expand=True)

    linhas_com = [titulo("Comunicados", 18)]
    for c in comunicados:
        linhas_com.append(ft.Column([
            ft.Text(c["titulo"], weight=ft.FontWeight.BOLD),
            ft.Text(c["conteudo"], size=12, color="#666666"),
            ft.Divider()
        ], spacing=3))
    bloco_com = cartao(ft.Column(linhas_com), expand=True)

    return ft.Column([
        titulo("Portal do Aluno"),
        indicadores,
        ft.Row([proximas, bloco_notas, bloco_com], spacing=15, expand=True)
    ], expand=True, spacing=18, scroll=ft.ScrollMode.AUTO)
