"""Dados acadêmicos adicionais. A matrícula continua vinculada à conta original."""
SCHEMA = (
    """CREATE TABLE IF NOT EXISTS unifica_perfis (
        matricula VARCHAR(60) PRIMARY KEY, ativo BOOLEAN NOT NULL DEFAULT TRUE,
        cargo VARCHAR(100) NOT NULL DEFAULT '', escola VARCHAR(150) NOT NULL DEFAULT '',
        departamento VARCHAR(100) NOT NULL DEFAULT '', telefone VARCHAR(40) NOT NULL DEFAULT '',
        tema VARCHAR(10) NOT NULL DEFAULT 'claro', fonte VARCHAR(10) NOT NULL DEFAULT 'normal',
        senha_em DATETIME NULL,
        FOREIGN KEY (matricula) REFERENCES unifica_contas(matricula) ON DELETE CASCADE)""",
    """CREATE TABLE IF NOT EXISTS unifica_turmas (
        id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(80) UNIQUE NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS unifica_eventos (
        id INT PRIMARY KEY AUTO_INCREMENT, titulo VARCHAR(150) NOT NULL, dia DATE NOT NULL,
        inicio TIME NOT NULL, fim TIME NOT NULL, descricao TEXT NOT NULL, INDEX(dia))""",
    """CREATE TABLE IF NOT EXISTS unifica_comunicados (
        id INT PRIMARY KEY AUTO_INCREMENT, titulo VARCHAR(150) NOT NULL, conteudo TEXT NOT NULL,
        publicacao DATETIME NOT NULL, status VARCHAR(20) NOT NULL, categoria VARCHAR(20) NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS unifica_notas (
        id INT PRIMARY KEY AUTO_INCREMENT, matricula VARCHAR(60) NOT NULL,
        disciplina VARCHAR(100) NOT NULL, periodo INT NOT NULL, nota DECIMAL(4,2) NOT NULL,
        aulas INT NOT NULL, faltas INT NOT NULL, UNIQUE(matricula,disciplina,periodo),
        FOREIGN KEY (matricula) REFERENCES unifica_contas(matricula) ON DELETE CASCADE)""",
    """CREATE TABLE IF NOT EXISTS unifica_atividade (
        id INT PRIMARY KEY AUTO_INCREMENT, momento DATETIME NOT NULL, acao VARCHAR(200) NOT NULL,
        tipo VARCHAR(20) NOT NULL, matricula VARCHAR(60) NOT NULL, INDEX(momento))""",
)


def initialize(store):
    for ddl in SCHEMA:
        store.query(ddl)
    store.query("""INSERT IGNORE INTO unifica_turmas(nome)
                   SELECT DISTINCT turma FROM unifica_contas WHERE turma<>''""")


def perfil(store, matricula):
    return (store.query("SELECT * FROM unifica_perfis WHERE matricula=?", (matricula,), rows=True) or [{}])[0]

