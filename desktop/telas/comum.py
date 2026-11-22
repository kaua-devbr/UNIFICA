import flet as ft
AZUL = "#303B83"
ROXO = "#D2D2F6"
ROXO_ESCURO = "#5146D8"
FUNDO = "#F7F7FC"
TEXTO = "#20243D"
VERDE = "#159B70"

def aplicar_estilo(page, controle, usuario):
    escuro = usuario.get("tema") == "escuro"
    fator = {"pequena": 0.875, "normal": 1, "grande": 1.15}.get(usuario.get("fonte"), 1)
    page.theme_mode = ft.ThemeMode.DARK if escuro else ft.ThemeMode.LIGHT
    page.bgcolor = "#191C2C" if escuro else FUNDO
    cores = {"white": "#282C40", "#F0F0FC": "#24283B", "#F1F4FA": "#363A50",
             "#D2D2F6": "#47456D", AZUL: "#BDC5FF", TEXTO: "#ECECFA",
             "#666666": "#CACADA", "#777777": "#CACADA", ROXO_ESCURO: "#B8AFFF"}
    def ajustar(item):
        if isinstance(item, ft.Text):
            item.size = (item.size or 14) * fator
            if escuro:
                item.color = cores.get(item.color, item.color)
        elif isinstance(item, (ft.TextField, ft.Dropdown)):
            item.text_size = (item.text_size or 14) * fator
        elif escuro and isinstance(item, ft.Container):
            item.bgcolor = cores.get(item.bgcolor, item.bgcolor)
        elif escuro and isinstance(item, ft.TextButton) and item.style:
            item.style.color = cores.get(item.style.color, item.style.color)
            item.style.bgcolor = cores.get(item.style.bgcolor, item.style.bgcolor)
        for child in getattr(item, "controls", []):
            ajustar(child)
        content = getattr(item, "content", None)
        if isinstance(content, ft.Control):
            ajustar(content)
    ajustar(controle)


def campo(rotulo, senha=False, valor=""):
    return ft.TextField(label=rotulo, password=senha, can_reveal_password=senha, value=valor, border_radius=12, border_color=ROXO_ESCURO, focused_border_color=AZUL, text_size=14)

def botao(texto, funcao, cor=ROXO_ESCURO, largura=None):
    return ft.Button(texto, on_click=funcao, width=largura, bgcolor=cor, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

def cartao(conteudo, largura=None, expand=False):
    return ft.Container(content=conteudo, padding=18, bgcolor="white", border_radius=14, width=largura, expand=expand, border=ft.Border.all(1, "#E7E7F1"))

def titulo(texto, tamanho=25):
    return ft.Text(texto, size=tamanho, weight=ft.FontWeight.BOLD, color=TEXTO)
