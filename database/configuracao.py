"""Configuração de conexão compartilhada pelo portal e pelo cliente local."""
import json
import os
import subprocess
import sys
from functools import lru_cache
from getpass import getpass
from pathlib import Path

import mysql.connector


class ConfiguracaoErro(Exception):
    pass


SUPORTE = "Na pasta do projeto, execute python app.py --configurar-banco (Linux/macOS: python3)."
PADRAO = {"host": "127.0.0.1", "port": 3306, "database": "UNIFICA", "user": "unifica_app"}
CAMPOS = (*PADRAO, "password")


def armazenar(valor=None):
    """Lê ou substitui uma única credencial por usuário do sistema."""
    try:
        if os.name == "nt":
            from auth.admin_local import converter, guardar
            arquivo = Path(os.environ["LOCALAPPDATA"]) / "UNIFICA" / "conexao.dpapi"
            if valor is None:
                return converter(arquivo.read_text("ascii"), False) if arquivo.exists() else None
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            guardar(arquivo, valor)
        elif sys.platform == "darwin":
            from keyring.backends.macOS import Keyring
            cofre = Keyring()
            if valor is None:
                return cofre.get_password("UNIFICA/MySQL", "conexao")
            cofre.set_password("UNIFICA/MySQL", "conexao", valor)
        else:
            args = ["secret-tool", "lookup"] if valor is None else [
                "secret-tool", "store", "--label=UNIFICA - conexão MySQL"]
            resultado = subprocess.run([*args, "application", "UNIFICA", "tipo", "mysql"],
                input=valor, capture_output=True, encoding="utf-8", timeout=60)
            if valor is None and resultado.returncode == 1 and not resultado.stderr.strip():
                return None
            resultado.check_returncode()
            return resultado.stdout.strip() if valor is None else None
    except Exception as erro:
        raise ConfiguracaoErro("Cofre do sistema indisponível. Consulte 'Suporte' no README.md.") from erro


def validar(dados):
    try:
        dados = {campo: dados[campo] for campo in CAMPOS}
        dados["port"] = int(dados["port"])
        if not 1 <= dados["port"] <= 65535 or not all(isinstance(dados[k], str)
            for k in ("host", "database", "user", "password")) or not all(
                dados[k].strip() for k in ("host", "database", "user")):
            raise ValueError()
        return dados
    except (KeyError, ValueError, TypeError) as erro:
        raise ConfiguracaoErro("Configuração do MySQL inválida. " + SUPORTE) from erro


def ambiente():
    return {campo: os.environ["MYSQL_" + campo.upper()] for campo in CAMPOS
            if "MYSQL_" + campo.upper() in os.environ}


@lru_cache(maxsize=1)
def configuracao():
    valores = ambiente()
    if "user" in valores and "password" in valores:
        return validar({**PADRAO, **valores})
    if valores:
        raise ConfiguracaoErro("Configuração de ambiente incompleta. Consulte 'Suporte' no README.md.")
    registro = armazenar()
    if not registro:
        raise ConfiguracaoErro("Primeiro acesso ao banco. " + SUPORTE)
    try:
        return validar(json.loads(registro))
    except ValueError as erro:
        raise ConfiguracaoErro("Registro local inválido. " + SUPORTE) from erro


def abrir(dados):
    return mysql.connector.connect(**dados, charset="utf8mb4", use_pure=True, connection_timeout=5)


def diagnostico(erro):
    motivo = {
        1044: "O usuário precisa de permissão nesse banco.",
        1045: "O MySQL recusou o usuário ou a senha.",
        1049: "Banco desconhecido. Confira o nome ou execute database/criar_banco.sql.",
        1142: "A conta precisa das permissões descritas no passo 3 do README.",
        1040: "Limite de conexões atingido. Confira as conexões ativas no servidor.",
        1054: "Coluna desconhecida. Compare a tabela existente com database/criar_banco.sql.",
        1062: "Já existe um registro com essa chave.",
        1146: "Tabela ausente. Confira o banco selecionado e o esquema da instalação.",
        1205: "A transação excedeu o tempo de espera por um bloqueio.",
        1213: "O MySQL desfez a transação após um conflito de bloqueios.",
        2006: "O servidor encerrou a conexão.",
        2013: "Conexão interrompida durante a operação.",
        2002: "Confira o serviço MySQL, o host e a porta.",
        2003: "Confira se o serviço MySQL está ligado e se o host e a porta estão corretos.",
        2005: "Confira o endereço do servidor MySQL.",
    }.get(erro.errno, "Consulte a seção de suporte do README.")
    return f"MySQL ({erro.errno}): {motivo}"


def configurar():
    if not sys.stdin.isatty():
        raise ConfiguracaoErro("Abra um terminal interativo para configurar o banco. " + SUPORTE)
    dados = {}
    for chave, rotulo in (("host", "Servidor"), ("port", "Porta"), ("database", "Banco"), ("user", "Usuário MySQL")):
        padrao = ambiente().get(chave, PADRAO[chave])
        dados[chave] = input(f"{rotulo} [{padrao}]: ").strip() or padrao
    dados["password"] = getpass("Senha desse usuário do MySQL: ")
    dados = validar(dados)
    conexao = abrir(dados)
    conexao.close()
    armazenar(json.dumps(dados, ensure_ascii=False))
    configuracao.cache_clear()
    print("Conexão testada e salva para seu usuário neste computador.")
    if ambiente():
        print("Variáveis MYSQL_* estão definidas neste terminal. Consulte 'Suporte' para usar o cofre.")


def preparar():
    if not ambiente() and sys.stdin.isatty() and not armazenar():
        configurar()


