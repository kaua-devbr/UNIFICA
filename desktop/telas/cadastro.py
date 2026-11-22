import flet as ft
from .comum import campo, botao, titulo

def mostrar_cadastro(page, ctx):
    ra,nome,email,turma,senha = (campo("Matrícula"),campo("Nome completo"),campo("E-mail"),
                                 campo("Turma"),campo("Senha inicial",True))
    def salvar(e):
        try:
            ctx["crud"].api("admin/aluno",dict(matricula=ra.value,nome=nome.value,email=email.value,
                            turma=turma.value,senha=senha.value,papel="aluno",ativo="1"))
            ctx["mostrar"]("/inicio")
            ctx["aviso"]("Aluno cadastrado. A matrícula já pode ser usada no portal.")
        except Exception as err:
            ctx["aviso"](str(err))
    page.clean()
    page.add(ft.Column([titulo("Cadastrar aluno"),ra,nome,email,turma,senha,botao("Cadastrar",salvar),
             ft.TextButton("Voltar",on_click=lambda e:ctx["mostrar"]("/inicio"))],scroll=ft.ScrollMode.AUTO))

