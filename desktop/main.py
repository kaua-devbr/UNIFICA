import flet as ft
from cliente import Cliente, ErroPortal, SessaoExpirada

from telas.comum import FUNDO, aplicar_estilo
from telas.login import mostrar_login
from telas import gestao
from telas.inicio import construir as inicio
from telas.perfil import construir as perfil
from telas.configuracoes import construir as configuracoes
from telas.sobre import construir as sobre
from telas.comunicados import construir as comunicados
from telas.notas import construir as notas
from telas.calendario import construir as calendario

AZUL = "#303B83"
ROXO = "#D2D2F6"
ROXO_ESCURO = "#5146D8"
TEXTO = "#20243D"


def main(page: ft.Page):
    page.title = "UNIFICA - Ambiente acadêmico"
    page.bgcolor = FUNDO
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 850
    page.window.min_height = 650

    # Informações e funções compartilhadas pelas telas.
    cliente = Cliente()
    ctx = {
        "usuario": None,
        "pagina_atual": "/login",
        "crud": cliente
    }

    def aviso(mensagem):
        page.show_dialog(ft.SnackBar(content=ft.Text(mensagem)))

    ctx["aviso"] = aviso

    def atualizar_usuario():
        if ctx["usuario"]:
            ctx["usuario"] = cliente.conta()

    ctx["atualizar_usuario"] = atualizar_usuario

    def estrutura(conteudo):
        usuario = ctx["usuario"] or {}

        itens_menu = [
            ("Início", "/inicio"),
            ("Notas e Frequência", "/notas"),
            ("Calendário", "/calendario"),
            ("Comunicados", "/comunicados"),
            ("Perfil", "/perfil"),
            ("Configurações", "/configuracoes"),
            ("Sobre o Sistema", "/sobre")
        ]

        if usuario.get("papel") == "administrador":
            itens_menu = gestao.MENU

        botoes = []

        for nome, rota in itens_menu:
            selecionado = ctx["pagina_atual"] == rota

            if selecionado:
                cor_texto = AZUL
                cor_fundo = ROXO
            else:
                cor_texto = TEXTO
                cor_fundo = None

            botao_menu = ft.TextButton(
                nome,
                on_click=lambda e, caminho=rota: mostrar(caminho),
                style=ft.ButtonStyle(
                    color=cor_texto,
                    bgcolor=cor_fundo,
                    padding=12
                )
            )

            item = ft.Container(
                content=botao_menu,
                bgcolor=cor_fundo,
                border_radius=8
            )
            botoes.append(item)

        botao_sair = ft.TextButton(
            "Sair da conta",
            on_click=lambda e: sair(),
            style=ft.ButtonStyle(color="#C43D4B")
        )

        menu = ft.Container(
            width=205,
            bgcolor="#F0F0FC",
            padding=12,
            content=ft.Column(
                [
                    ft.Text(
                        "UN",
                        size=48,
                        weight=ft.FontWeight.BOLD,
                        color=ROXO_ESCURO
                    ),
                    ft.Text(
                        "UNIFICA",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO
                    ),
                    ft.Text("Ambiente acadêmico", size=11, color="#666666"),
                    ft.Divider(),
                    *botoes,
                    botao_sair
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=7
            )
        )

        nome_usuario = usuario.get("apelido") or usuario.get("nome") or ""

        topo = ft.Container(
            padding=ft.Padding.only(left=22, right=22, top=15, bottom=10),
            content=ft.Row(
                [
                    ft.Text(
                        "Portal do Administrador" if usuario.get("papel") == "administrador" else "Portal do Aluno",
                        size=19,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        nome_usuario,
                        color=AZUL,
                        weight=ft.FontWeight.BOLD
                    )
                ]
            )
        )

        area_principal = ft.Column(
            [
                topo,
                ft.Container(expand=True, padding=20, content=conteudo)
            ],
            expand=True,
            spacing=0
        )

        return ft.Row(
            [menu, ft.Container(expand=True, content=area_principal)],
            expand=True,
            spacing=0
        )

    def mostrar(rota):
        if not ctx["usuario"]:
            mostrar_login(page, ctx)
            return

        try:
            atualizar_usuario()
        except SessaoExpirada as erro:
            mostrar_login(page, ctx)
            aviso(str(erro))
            return
        except ErroPortal as erro:
            aviso(str(erro))
            return
        if not ctx["usuario"]:
            mostrar_login(page, ctx)
            return
        ctx["pagina_atual"] = rota


        telas = {
            "/inicio": inicio,
            "/perfil": perfil,
            "/configuracoes": configuracoes,
            "/sobre": sobre,
            "/comunicados": comunicados,
            "/notas": notas,
            "/calendario": calendario
        }

        try:
            if ctx["usuario"]["papel"] == "administrador" and rota != "/configuracoes":
                conteudo = gestao.construir(page, ctx, rota)
            else:
                conteudo = telas.get(rota, inicio)(page, ctx)
        except SessaoExpirada as erro:
            mostrar_login(page, ctx)
            aviso(str(erro))
            return
        except ErroPortal as erro:
            aviso(str(erro))
            return

        arvore = estrutura(conteudo)
        aplicar_estilo(page, arvore, ctx["usuario"])
        page.clean()
        page.add(arvore)
        page.update()

    def sair():
        try:
            cliente.sair()
        finally:
            mostrar_login(page,ctx)

    ctx["mostrar"] = mostrar
    ctx["mostrar_login"] = lambda: mostrar_login(page, ctx)

    mostrar_login(page, ctx)


if __name__ == "__main__":
    ft.run(main)