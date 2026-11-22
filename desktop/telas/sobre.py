import flet as ft
from .comum import *

def construir(page, ctx):
    usuario = ctx["usuario"]
    crud = ctx["crud"]
    return ft.Column([
        titulo("Sobre o Sistema"),
        cartao(ft.Text("Última atualização: 06 de novembro de 2026", size=16)),
        cartao(ft.Text("Versão atual: 0.1", size=16)),
        ft.Text("UNIFICA - Ambiente acadêmico", color="#777777")
    ], spacing=18)
