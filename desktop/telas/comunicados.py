import flet as ft
from .comum import *

def construir(page, ctx):
    usuario = ctx["usuario"]
    crud = ctx["crud"]
    comunicados = crud.api("comunicados")["itens"]
    itens = [titulo("Comunicados")]
    if not comunicados:
        itens.append(ft.Text("Nenhum comunicado cadastrado."))
    for c in comunicados:
        data = c["publicacao"][:10]
        itens.append(cartao(ft.Column([
            ft.Row([
                ft.Text(c["titulo"], weight=ft.FontWeight.BOLD, size=17, expand=True),
                ft.Text("/".join(reversed(data.split("-"))), color="#777777")
            ]),
            ft.Text(c["conteudo"])
        ], spacing=8)))
    return ft.Column(itens, spacing=12, scroll=ft.ScrollMode.AUTO)
