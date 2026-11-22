import flet as ft
from portal_url import endereco
from .comum import campo, botao, titulo, ROXO_ESCURO

def mostrar_login(page, ctx):
    ctx["usuario"] = None
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F7F7FC"
    crud = ctx["crud"]
    ctx["pagina_atual"] = "/login"
    matricula = campo("Matrícula")
    senha = campo("Senha", True)

    def entrar(e):
        try:
            encontrado = crud.login(matricula.value.strip(), senha.value)
            if encontrado:
                ctx["usuario"] = encontrado
                ctx["mostrar"]("/visao" if encontrado["papel"] == "administrador" else "/inicio")
            else:
                ctx["aviso"]("Matrícula ou senha incorretos.")
        except Exception as erro:
            ctx["aviso"](str(erro))

    page.clean()
    page.add(
        ft.Container(
            expand=True, alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=430, padding=35, bgcolor="white", border_radius=22,
                content=ft.Column(
                    [
                        ft.Text("UN", size=58, weight=ft.FontWeight.BOLD,
                                color=ROXO_ESCURO, text_align=ft.TextAlign.CENTER),
                        titulo("UNIFICA", 27),
                        ft.Text("Ambiente acadêmico", color="#777777"),
                        ft.Container(height=25),
                        titulo("BEM-VINDO", 30),
                        ft.Container(height=10),
                        matricula, senha,
                        botao("LOGIN", entrar, largura=180),
                        ft.TextButton("Abrir portal", url=endereco()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                )
            )
        )
    )
    page.update()
