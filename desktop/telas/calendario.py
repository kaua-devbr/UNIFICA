import flet as ft
from datetime import date, datetime
import calendar
from .comum import *

def construir(page, ctx):
    crud = ctx["crud"]
    aviso = ctx["aviso"]
    hoje = date.today()
    mes_atual = {"mes": hoje.month, "ano": hoje.year}
    selecionada = {"data": hoje}

    nome_mes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    calendario_coluna = ft.Column(spacing=8)
    eventos_coluna = ft.Column(spacing=10)
    texto_mes = ft.Text("", size=20, weight=ft.FontWeight.BOLD)

    def carregar_eventos():
        eventos_coluna.controls.clear()
        try:
            eventos = crud.api(f"eventos?mes={mes_atual['mes']}&ano={mes_atual['ano']}")["itens"]
            eventos_dia = [ev for ev in eventos
                           if str(ev["dia"]) == selecionada["data"].isoformat()]
            if not eventos_dia:
                eventos_coluna.controls.append(ft.Text("Nenhum evento nesta data."))
            for ev in eventos_dia:
                eventos_coluna.controls.append(cartao(ft.Column([
                    ft.Text(f"{ev['inicio']} – {ev['fim']}", color=ROXO_ESCURO),
                    ft.Text(ev["titulo"], weight=ft.FontWeight.BOLD)
                ])))
        except Exception as erro:
            eventos_coluna.controls.append(ft.Text(str(erro)))

    def selecionar_dia(dia):
        selecionada["data"] = date(mes_atual["ano"], mes_atual["mes"], dia)
        desenhar_calendario()

    def desenhar_calendario():
        calendario_coluna.controls.clear()
        texto_mes.value = f"{nome_mes[mes_atual['mes']-1]} de {mes_atual['ano']}"
        calendario_coluna.controls.append(texto_mes)
        dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        calendario_coluna.controls.append(ft.Row([
            ft.Container(ft.Text(d, weight=ft.FontWeight.BOLD), expand=True,
                         alignment=ft.Alignment(0, 0)) for d in dias
        ]))
        semanas = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(mes_atual["ano"], mes_atual["mes"])
        for semana in semanas:
            celulas = []
            for dia in semana:
                if dia == 0:
                    celulas.append(ft.Container(expand=True, height=48))
                else:
                    escolhido = selecionada["data"].day == dia
                    celulas.append(ft.Container(
                        content=ft.TextButton(
                            str(dia),
                            on_click=lambda e, d=dia: selecionar_dia(d),
                            style=ft.ButtonStyle(
                                color="white" if escolhido else TEXTO,
                                bgcolor=ROXO_ESCURO if escolhido else "#F1F4FA"
                            )
                        ),
                        expand=True, height=48, alignment=ft.Alignment(0, 0)
                    ))
            calendario_coluna.controls.append(ft.Row(celulas, spacing=4))
        carregar_eventos()
        page.update()

    def mudar_mes(quantidade):
        novo = mes_atual["mes"] + quantidade
        if novo < 1:
            mes_atual["mes"] = 12
            mes_atual["ano"] -= 1
        elif novo > 12:
            mes_atual["mes"] = 1
            mes_atual["ano"] += 1
        else:
            mes_atual["mes"] = novo
        selecionada["data"] = date(mes_atual["ano"], mes_atual["mes"], 1)
        desenhar_calendario()

    botoes_mes = ft.Row([
        ft.TextButton("Anterior", on_click=lambda e: mudar_mes(-1)),
        ft.Container(expand=True),
        ft.TextButton("Próximo", on_click=lambda e: mudar_mes(1))
    ])
    desenhar_calendario()
    return ft.Column([
        titulo("Calendário"),
        ft.Row([
            cartao(ft.Column([botoes_mes, calendario_coluna]), expand=True),
            cartao(ft.Column([
                titulo("Eventos do dia", 18), eventos_coluna,
            ]), largura=330)
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
    ], expand=True, spacing=15, scroll=ft.ScrollMode.AUTO)
