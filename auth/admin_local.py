"""Lembrete local da senha do portal, protegido pela conta do sistema."""
import base64
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
        encoding="ascii", capture_output=True, check=True, timeout=15,
        env={**os.environ, "PSModulePath": str(ps.parent / "Modules")})
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


def credencial(pasta, senha=None):
    arquivo = pasta / "admin.dpapi"
    if os.name == "nt":
        if senha is not None:
            guardar(arquivo, senha)
        elif arquivo.is_file():
            return converter(arquivo.read_text(encoding="ascii"), False)
        return None
    identificador = str(pasta.resolve())
    if sys.platform == "darwin":
        from keyring.backends.macOS import Keyring
        cofre = Keyring()
        if senha is None:
            return cofre.get_password("UNIFICA/portal-admin", identificador)
        cofre.set_password("UNIFICA/portal-admin", identificador, senha)
        return None
    atributos = ["application", "UNIFICA", "tipo", "portal-admin", "instancia", identificador]
    if senha is None:
        r = subprocess.run(["secret-tool", "lookup", *atributos], capture_output=True, timeout=15)
        if r.returncode == 1 and not r.stderr.strip():
            return None
        r.check_returncode()
        return base64.b64decode(r.stdout.strip(), validate=True).decode()
    subprocess.run(["secret-tool", "store", "--label=UNIFICA - administrador", *atributos],
                   input=base64.b64encode(senha.encode()), capture_output=True, check=True, timeout=15)


def salvar_lembrete(pasta, senha):
    try:
        credencial(pasta, senha)
    except Exception:
        print("Senha do portal atualizada no banco. Cofre local indisponível para guardar o lembrete.", flush=True)


def mostrar(store, pasta, inicial=None):
    if not sys.stdout.isatty():
        return
    conta = store.account("admin")
    if not conta or conta["papel"] != "administrador":
        return
    senha = inicial
    if not senha:
        try:
            candidata = credencial(pasta)
        except Exception:
            candidata = None
        if candidata and check_password_hash(conta["senha"], candidata):
            print(f"Login: admin\nSenha: {candidata}", flush=True)
            return
        if not sys.stdin.isatty():
            print("Para ativar o lembrete, abra app.py em um terminal interativo.")
            return
    if not senha:
        escolha = input("Senha do portal admin: [G] guardar a atual, [R] redefinir ou [Enter] guardar a atual: ").strip().lower()
        if escolha in ("g", ""):
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
    print(f"Login: admin\nSenha: {senha}", flush=True)
    salvar_lembrete(pasta, senha)
