"""Cadastro e manutenção de alunos no MySQL do UNIFICA."""
from contextlib import closing

from werkzeug.security import generate_password_hash

from database.store import Store


def cadastrar_aluno(matricula, nome, email, turma, senha):
    sql = """
        INSERT INTO unifica_contas (matricula, nome, email, turma, papel, senha)
        VALUES (%s, %s, %s, %s, 'aluno', %s)
    """
    valores = (matricula, nome, email, turma, generate_password_hash(senha))
    with Store().connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(sql, valores)


def listar_alunos():
    sql = """
        SELECT matricula, nome, email, turma FROM unifica_contas
        WHERE papel = 'aluno' ORDER BY nome, matricula
    """
    with Store().connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def buscar_aluno(matricula):
    sql = """
        SELECT matricula, nome, email, turma FROM unifica_contas
        WHERE matricula = %s AND papel = 'aluno'
    """
    with Store().connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(sql, (matricula,))
        return cursor.fetchone()


def atualizar_aluno(matricula, nome, email, turma):
    sql = """
        UPDATE unifica_contas SET nome = %s, email = %s, turma = %s
        WHERE matricula = %s AND papel = 'aluno'
    """
    with Store().connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(sql, (nome, email, turma, matricula))


def deletar_aluno(matricula):
    with Store().connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(
            "SELECT matricula FROM unifica_contas WHERE matricula = %s AND papel = 'aluno' FOR UPDATE",
            (matricula,),
        )
        if cursor.fetchone() is not None:
            cursor.execute("DELETE FROM unifica_sessoes WHERE matricula = %s", (matricula,))
            cursor.execute("DELETE FROM unifica_contas WHERE matricula = %s AND papel = 'aluno'", (matricula,))
