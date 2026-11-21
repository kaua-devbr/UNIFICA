import os
from contextlib import contextmanager

import mysql.connector


def conectar():
    """Abre uma conexão com o MySQL. O crud.py e o resto do projeto usam esta mesma função."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE", "UNIFICA"),
        use_pure=True,
        charset="utf8mb4",
        connection_timeout=5,
    )


class Store:
    @contextmanager
    def connection(self):
        conn = conectar()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def query(self, sql, params=(), *, rows=False):
        with self.connection() as conn:
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(sql.replace("?", "%s"), params)
                if rows:
                    return [dict(row) for row in cur.fetchall()]
                return cur.rowcount
            finally:
                cur.close()

    def initialize(self):
        self.query("""CREATE TABLE IF NOT EXISTS unifica_contas (
            matricula VARCHAR(60) PRIMARY KEY, nome VARCHAR(150) NOT NULL,
            email VARCHAR(254) NOT NULL, turma VARCHAR(80) NOT NULL,
            papel VARCHAR(20) NOT NULL, senha VARCHAR(255) NOT NULL)""")
        self.query("""CREATE TABLE IF NOT EXISTS unifica_sessoes (
            token CHAR(64) PRIMARY KEY, matricula VARCHAR(60) NOT NULL,
            expira BIGINT NOT NULL, FOREIGN KEY (matricula)
            REFERENCES unifica_contas(matricula))""")

    def account(self, matricula):
        rows = self.query("SELECT * FROM unifica_contas WHERE matricula=?", (matricula,), rows=True)
        return rows[0] if rows else None

    def create(self, matricula, nome, email, turma, papel, password):
        from werkzeug.security import generate_password_hash
        self.query("INSERT INTO unifica_contas (matricula,nome,email,turma,papel,senha) VALUES (?,?,?,?,?,?)",
                   (matricula, nome, email, turma, papel, generate_password_hash(password)))
