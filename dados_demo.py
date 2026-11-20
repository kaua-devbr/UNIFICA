
from datetime import date

AULAS_DEMO = 120
DISCIPLINAS_DEMO = (
    ("Artes", 9.0, 0),
    ("Biologia", 7.5, 1),
    ("Educação Física", 7.0, 0),
    ("Filosofia", 8.5, 1),
    ("Física", 6.0, 0),
    ("Geografia", 9.5, 1),
    ("História", 7.5, 1),
    ("Inglês", 6.0, 0),
    ("Matemática", 7.5, 0),
    ("Português", 6.5, 2),
    ("Química", 7.0, 0),
    ("Sociologia", 8.5, 1),
    ("Aprof. TICs", 8.0, 4),
    ("Aprof. TICs I", 8.5, 0),
    ("Atividade Comp.", None, 0),
    ("Criat. e Inovação", 7.5, 1),
    ("Eletiva", 9.0, 2),
    ("Eng. de Software", 7.0, 0),
    ("Letramento", 8.5, 0),
    ("PNT - DESKTOP", 7.0, 1),
    ("PNT - WEB", 9.0, 4),
    ("PTS", 7.5, 0),
    ("STEM", 6.5, 2),
)

MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
)
DIAS = ("Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo")
EVENTOS = {
    date(2026, 11, 6): [
        ("09:00–10:00", "Reunião de Alinhamento Semanal"),
        ("14:30–16:00", "Apresentação do Projeto"),
    ],
    date(2026, 11, 9): [("10:00", "Atividade de Geografia")],
    date(2026, 11, 12): [("14:00", "Entrega de PNT Desktop")],
    date(2026, 11, 16): [("09:00", "Reunião de turma")],
    date(2026, 11, 20): [("10:00", "Aulão para o Enem")],
    date(2026, 11, 25): [("13:00", "Apresentações da turma")],
    date(2026, 11, 30): [("09:00", "Encerramento do mês")],
}
CATEGORIAS = {
    "todos": "Todos",
    "prazos": "Prazos e Entregas",
    "avisos": "Avisos Importantes",
    "calendario": "Calendário",
}
COMUNICADOS = [
    (1, "calendario", "Calendário Acadêmico", "Confira as novas datas do calendário acadêmico.", "Há 2 dias"),
    (2, "prazos", "Atividade Pendente", "Entrega do trabalho de Geografia até sexta-feira.", "Há 3 dias"),
    (3, "avisos", "Aviso Importante", "Mudança na sala de aula de Programação.", "Há 1 semana"),
    (4, "prazos", "Atividade Pendente", "Entrega do trabalho de PNT Desktop até amanhã.", "Há 2 semanas"),
    (5, "avisos", "Aviso Importante", "Aulão para o Enem na próxima quinta-feira.", "Há 3 semanas"),
]
