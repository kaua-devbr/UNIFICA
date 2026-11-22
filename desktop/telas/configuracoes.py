import flet as ft
from .comum import *

def construir(page, ctx):
    usuario = ctx["usuario"]
    crud = ctx["crud"]
    aviso = ctx["aviso"]
    atualizar_usuario = ctx["atualizar_usuario"]
    senha_atual = campo("Senha atual", True)
    senha_nova = campo("Nova senha", True)
    confirmar = campo("Confirmar nova senha", True)
    tema = ft.Dropdown(
        label="Tema", value=usuario.get("tema") or "claro", editable=False,
        options=[ft.DropdownOption(key="claro", text="Claro"),
                 ft.DropdownOption(key="escuro", text="Escuro")],
    )
    fonte = ft.Dropdown(
        label="Tamanho da fonte", value=usuario.get("fonte") or "normal", editable=False,
        options=[ft.DropdownOption(key="pequena", text="Pequena"),
                 ft.DropdownOption(key="normal", text="Normal"),
                 ft.DropdownOption(key="grande", text="Grande")],
    )

    def mudar_senha(e):
        if senha_nova.value != confirmar.value or not senha_nova.value:
            aviso("Confira a nova senha e a confirmação.")
            return
        try:
            crud.alterar_senha(senha_atual.value, senha_nova.value)
            ctx["mostrar_login"]()
            aviso("Senha alterada. Entre com a nova senha.")
        except Exception as erro:
            aviso(str(erro))

    def salvar_estilo(e):
        try:
            crud.api("preferencias", dict(tema=tema.value, fonte=fonte.value))
            ctx["mostrar"]("/configuracoes")
            aviso("Preferências salvas.")
        except Exception as erro:
            aviso(str(erro))

    return ft.Column([
        titulo("Configurações"),
        cartao(ft.Column([
            titulo("Segurança da conta", 20),
            senha_atual, senha_nova, confirmar,
            botao("Alterar senha", mudar_senha)
        ])),
        cartao(ft.Column([
            titulo("Estilo de Página", 20),
            tema, fonte,
            botao("Salvar preferências", salvar_estilo)
        ]))
    ], spacing=20, scroll=ft.ScrollMode.AUTO)
