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
    linhas = [
        ft.Row([
            ft.Text("Disciplina", weight=ft.FontWeight.BOLD, expand=True),
            ft.Text("Nota", weight=ft.FontWeight.BOLD, width=70),
            ft.Text("Situação", weight=ft.FontWeight.BOLD, width=110),
            ft.Text("Faltas", weight=ft.FontWeight.BOLD, width=60)
        ])
    ]
    for n in notas:
        linhas.append(ft.Row([
            ft.Text(f"{n['disciplina']} · {n['periodo']}º bim.", expand=True),
            ft.Text(str(n["nota"]), width=70),
            ft.Text("Aprovado" if float(n["nota"]) >= 6 else "Abaixo da média", color=VERDE, width=110),
            ft.Text(str(n["faltas"]), width=60)
        ]))
    return ft.Column([
        titulo("Notas e Frequência"),
        ft.Row([
            cartao(ft.Column([ft.Text("Média Geral"), titulo(
                media_texto, 25)]), expand=True),
            cartao(ft.Column([ft.Text("Frequência"), titulo(freq_texto, 25)]),
                   expand=True)
        ]),
        cartao(ft.Column(linhas, spacing=12), expand=True)
    ], expand=True, spacing=18, scroll=ft.ScrollMode.AUTO)
