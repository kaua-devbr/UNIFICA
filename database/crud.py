from werkzeug.security import generate_password_hash
from database.store import conectar


def cadastrar_aluno(matricula, nome, email, turma, senha):
    conexao = conectar()
    cursor = conexao.cursor()
    cadastro = "INSERT INTO unifica_contas (matricula, nome, email, turma, papel, senha) VALUES (%s, %s, %s, %s, %s, %s)"
    valores = (matricula, nome, email, turma, "aluno", generate_password_hash(senha))
    cursor.execute(cadastro, valores)
    conexao.commit()
    cursor.close()
    conexao.close()


def listar_alunos():
    conexao = conectar()
    cursor = conexao.cursor()
    consultar = "SELECT matricula, nome, email, turma FROM unifica_contas WHERE papel = %s ORDER BY nome"
    cursor.execute(consultar, ("aluno",))
    alunos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return alunos


def buscar_aluno(matricula):
    conexao = conectar()
    cursor = conexao.cursor()
    consultar = "SELECT matricula, nome, email, turma FROM unifica_contas WHERE matricula = %s AND papel = %s"
    cursor.execute(consultar, (matricula, "aluno"))
    aluno = cursor.fetchone()
    cursor.close()
    conexao.close()
    return aluno


def atualizar_aluno(matricula, nome, email, turma):
    conexao = conectar()
    cursor = conexao.cursor()
    atualizar = "UPDATE unifica_contas SET nome = %s, email = %s, turma = %s WHERE matricula = %s AND papel = %s"
    valores = (nome, email, turma, matricula, "aluno")
    cursor.execute(atualizar, valores)
    conexao.commit()
    cursor.close()
    conexao.close()


def deletar_aluno(matricula):
    conexao = conectar()
    cursor = conexao.cursor()
    # só mexe em contas de aluno (nunca no administrador)
    cursor.execute("SELECT matricula FROM unifica_contas WHERE matricula = %s AND papel = %s", (matricula, "aluno"))
    if cursor.fetchone() is not None:
        # a tabela de sessões depende da conta, então apaga ela primeiro
        cursor.execute("DELETE FROM unifica_sessoes WHERE matricula = %s", (matricula,))
        cursor.execute("DELETE FROM unifica_contas WHERE matricula = %s AND papel = %s", (matricula, "aluno"))
        conexao.commit()
    cursor.close()
    conexao.close()
