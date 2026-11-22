import flet as ft
from .comum import campo, botao, titulo, cartao

def construir(page,ctx):
    usuario = ctx["usuario"]
    nome = campo("Nome completo", valor=usuario["nome"])
    email = campo("E-mail", valor=usuario["email"])
    escola = campo("Escola", valor=usuario["escola"])
    def salvar(e):
        try:
            ctx["crud"].api("perfil",dict(nome=nome.value,email=email.value,escola=escola.value))
            ctx["mostrar"]("/perfil")
            ctx["aviso"]("Perfil atualizado.")
        except Exception as err:
            ctx["aviso"](str(err))
    return ft.Column([titulo("Meu perfil"), ft.Text(f"Matrícula: {usuario['matricula']}"),
        ft.Text(f"Turma: {usuario['turma'] or '—'}"), cartao(ft.Column([nome,email,escola])),
        botao("Salvar alterações",salvar)],scroll=ft.ScrollMode.AUTO)

