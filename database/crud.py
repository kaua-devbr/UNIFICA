"""Cadastro, consulta, atualização e exclusão de alunos do UNIFICA."""
from contextlib import closing
from werkzeug.security import generate_password_hash


def _sql(banco, comando):
    """O MySQL usa %s e o SQLite usa ? para receber os valores."""
    if banco.mysql:
        return comando
    return comando.replace("%s", "?")


def criar_aluno(banco, matricula, nome, email, turma, senha):
    cadastro = """
        INSERT INTO unifica_contas (matricula, nome, email, turma, papel, senha)
        VALUES (%s, %s, %s, %s, 'aluno', %s)
    """
    valores = (matricula, nome, email, turma, generate_password_hash(senha))

    with banco.connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(_sql(banco, cadastro), valores)


def listar_alunos(banco):
    consulta = """
        SELECT matricula, nome, email, turma
        FROM unifica_contas
        WHERE papel = 'aluno'
        ORDER BY nome, matricula
    """
    with banco.connection() as conexao:
        cursor = conexao.cursor(dictionary=True) if banco.mysql else conexao.cursor()
        with closing(cursor):
            cursor.execute(consulta)
            return [dict(aluno) for aluno in cursor.fetchall()]


def buscar_aluno(banco, matricula):
    consulta = """
        SELECT matricula, nome, email, turma
        FROM unifica_contas
        WHERE matricula = %s AND papel = 'aluno'
    """
    valores = (matricula,)

    with banco.connection() as conexao:
        cursor = conexao.cursor(dictionary=True) if banco.mysql else conexao.cursor()
        with closing(cursor):
            cursor.execute(_sql(banco, consulta), valores)
            aluno = cursor.fetchone()
            return dict(aluno) if aluno is not None else None


def atualizar_aluno(banco, matricula, nome, email, turma):
    atualizar = """
        UPDATE unifica_contas
        SET nome = %s, email = %s, turma = %s
        WHERE matricula = %s AND papel = 'aluno'
    """
    valores = (nome, email, turma, matricula)

    with banco.connection() as conexao, closing(conexao.cursor()) as cursor:
        cursor.execute(_sql(banco, atualizar), valores)
        if cursor.rowcount > 0:
            return True

        # O MySQL pode retornar zero quando o aluno já possui os mesmos dados.
        consulta = "SELECT 1 FROM unifica_contas WHERE matricula = %s AND papel = 'aluno'"
        cursor.execute(_sql(banco, consulta), (matricula,))
        return cursor.fetchone() is not None


def excluir_aluno(banco, matricula):
    consulta = "SELECT matricula FROM unifica_contas WHERE matricula = %s AND papel = 'aluno'"
    deletar_sessoes = "DELETE FROM unifica_sessoes WHERE matricula = %s"
    deletar_aluno = "DELETE FROM unifica_contas WHERE matricula = %s AND papel = 'aluno'"
    valores = (matricula,)

    with banco.connection() as conexao, closing(conexao.cursor()) as cursor:
        # Bloqueia a conta durante a exclusão das sessões e do próprio aluno.
        if banco.mysql:
            consulta += " FOR UPDATE"
        else:
            cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(_sql(banco, consulta), valores)
        if cursor.fetchone() is None:
            return False

        cursor.execute(_sql(banco, deletar_sessoes), valores)
        cursor.execute(_sql(banco, deletar_aluno), valores)
        return cursor.rowcount == 1
