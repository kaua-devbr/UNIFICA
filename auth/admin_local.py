"""Lembrete local da senha do portal, protegido pelo usuário do Windows."""
import base64
import binascii
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from getpass import getpass

from werkzeug.security import check_password_hash, generate_password_hash


def converter(valor, proteger):
    # Só o stdin transporta o conteúdo; a linha de comando é fixa.
    comando = (
        "$texto=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String([Console]::ReadLine()));"
        "$seguro=ConvertTo-SecureString $texto -AsPlainText -Force;"
        "ConvertFrom-SecureString $seguro"
        if proteger else
        "$seguro=ConvertTo-SecureString ([Console]::ReadLine());"
        "$texto=[Net.NetworkCredential]::new('', $seguro).Password;"
        "[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($texto))"
    )
    entrada = base64.b64encode(valor.encode()).decode() if proteger else valor
    ps = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    resultado = subprocess.run([str(ps), "-NoProfile", "-NonInteractive", "-Command",
        "$ErrorActionPreference='Stop';" + comando], input=entrada+"\n",
        encoding="ascii", capture_output=True, check=True, timeout=15)
    saida = resultado.stdout.strip()
    return saida if proteger else base64.b64decode(saida, validate=True).decode()


def guardar(arquivo, senha):
    protegido = converter(senha, True)
    with tempfile.NamedTemporaryFile(dir=arquivo.parent, delete=False, mode="w", encoding="ascii") as temp:
        caminho = Path(temp.name)
    try:
        caminho.write_text(protegido, encoding="ascii")
        caminho.replace(arquivo)
    finally:
        caminho.unlink(missing_ok=True)


def mostrar(store, pasta, inicial=None):
    if os.name != "nt" or not sys.stdin.isatty() or not sys.stdout.isatty():
        return
    conta = store.account("admin")
    if not conta or conta["papel"] != "administrador":
        return
    arquivo = pasta / "admin.dpapi"
    senha = inicial
    if not senha and arquivo.is_file():
        try:
            candidata = converter(arquivo.read_text(encoding="ascii"), False)
            if check_password_hash(conta["senha"], candidata):
                print(f"Portal | matrícula: admin | senha: {candidata}", flush=True)
                return
        except (OSError, subprocess.SubprocessError, UnicodeError, binascii.Error):
            pass
    if not senha:
        escolha = input("Senha do portal admin: [G] guardar a atual, [R] redefinir ou [Enter] continuar: ").strip().lower()
        if escolha == "g":
            senha = getpass("Senha atual do portal admin: ")
            if not check_password_hash(conta["senha"], senha):
                print("Senha incorreta. Iniciando o portal.")
                return
        elif escolha == "r":
            if input("Para trocar a senha do admin e encerrar suas sessões, digite REDEFINIR: ").strip() != "REDEFINIR":
                return
            senha = secrets.token_urlsafe(15)
            with store.connection() as conn, conn.cursor() as cur:
                cur.execute("UPDATE unifica_contas SET senha=%s WHERE matricula=%s AND senha=%s AND papel=%s",
                            (generate_password_hash(senha),"admin",conta["senha"],"administrador"))
                if cur.rowcount != 1:
                    print("A conta mudou durante a operação. Inicie novamente.")
                    return
                cur.execute("DELETE FROM unifica_sessoes WHERE matricula=%s", ("admin",))
                cur.execute("""INSERT INTO unifica_perfis(matricula,senha_em) VALUES(%s,NOW())
                               ON DUPLICATE KEY UPDATE senha_em=NOW()""", ("admin",))
        else:
            return
        print(f"Portal | matrícula: admin | senha: {senha}", flush=True)
    try:
        guardar(arquivo, senha)
    except (OSError, subprocess.SubprocessError):
        print("Não foi possível guardar o lembrete nesta conta do Windows.")
