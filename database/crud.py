


def criar_aluno(banco, matricula, nome, email, turma, senha):

    banco.create(matricula, nome, email, turma, "aluno", senha)


def listar_alunos(banco):
    return banco.query(
        "SELECT matricula, nome, email, turma FROM unifica_contas "
        "WHERE papel = 'aluno' ORDER BY nome, matricula",
        rows=True,
    )


def buscar_aluno(banco, matricula):
    linhas = banco.query(
        "SELECT matricula, nome, email, turma FROM unifica_contas "
        "WHERE papel = 'aluno' AND matricula = ?", (matricula,), rows=True,
    )
    return linhas[0] if linhas else None


def atualizar_aluno(banco, matricula, nome, email, turma):
    alteradas = banco.query(
        "UPDATE unifica_contas SET nome = ?, email = ?, turma = ? "
        "WHERE papel = 'aluno' AND matricula = ?", (nome, email, turma, matricula),
    )

    return bool(alteradas) or buscar_aluno(banco, matricula) is not None


def excluir_aluno(banco, matricula):
    
    parametro = "%s" if banco.mysql else "?"
    with banco.connection() as conexao:
        cursor = conexao.cursor()
        try:
            if not banco.mysql:
                cursor.execute("BEGIN IMMEDIATE")
            consulta = f"SELECT matricula FROM unifica_contas WHERE papel = 'aluno' AND matricula = {parametro}"
            if banco.mysql:
                consulta += " FOR UPDATE"
            cursor.execute(consulta, (matricula,))
            if cursor.fetchone() is None:
                return False
            cursor.execute(f"DELETE FROM unifica_sessoes WHERE matricula = {parametro}", (matricula,))
            cursor.execute(f"DELETE FROM unifica_contas WHERE papel = 'aluno' AND matricula = {parametro}", (matricula,))
            return cursor.rowcount == 1
        finally:
            cursor.close()
