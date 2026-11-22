"""Instalação local do portal UNIFICA (Python e MySQL Server em execução)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from getpass import getpass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor"))

from mysql.connector import Error
from database.configuracao import (ConfiguracaoErro, abrir, ambiente, armazenar,
                                    configurar, configuracao, diagnostico, validar)


def preparar_tls():
    mkcert = shutil.which("mkcert")
    if not mkcert and sys.platform == "win32":
        subprocess.run(["winget", "install", "--id", "FiloSottile.mkcert", "--exact",
                        "--source", "winget", "--accept-package-agreements",
                        "--accept-source-agreements"], check=True)
        link = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Links/mkcert.exe"
        mkcert = shutil.which("mkcert") or (str(link) if link.is_file() else None)
    elif sys.platform.startswith("linux") and shutil.which("apt-get"):
        faltam = [pacote for programa, pacote in (("mkcert", "mkcert"), ("certutil", "libnss3-tools"),
                  ("secret-tool", "libsecret-tools")) if not shutil.which(programa)]
        if faltam:
            subprocess.run(["sudo", "apt-get", "install", "-y", *faltam], check=True)
        mkcert = shutil.which("mkcert")
    elif not mkcert and sys.platform == "darwin" and shutil.which("brew"):
        subprocess.run(["brew", "install", "mkcert"], check=True)
        mkcert = shutil.which("mkcert")
    if not mkcert:
        raise ConfiguracaoErro("Instale mkcert pelo gerenciador de pacotes, reabra o terminal e repita a instalação.")
    subprocess.run([mkcert, "-install"], check=True)
    ca = Path(subprocess.check_output([mkcert, "-CAROOT"], text=True).strip()) / "rootCA.pem"
    pasta = ROOT / "instance/tls"
    pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=pasta) as td:
        temporario = Path(td)
        subprocess.run([mkcert, "-cert-file", str(temporario/"cert.pem"), "-key-file",
                        str(temporario/"key.pem"), "127.0.0.1", "localhost"], check=True)
        shutil.copyfile(ca, temporario/"ca.pem")
        for nome in ("key.pem", "cert.pem", "ca.pem"):
            (temporario/nome).replace(pasta/nome)


def criar_base():
    porta = input("Porta do MySQL local [3306]: ").strip() or "3306"
    dados = validar(dict(host="127.0.0.1", port=porta, database="UNIFICA",
                         user="unifica_app", password=getpass("Escolha ou informe a senha MySQL de unifica_app: ")))
    if not dados["password"]:
        raise ConfiguracaoErro("Informe uma senha para unifica_app.")
    admin = input("Administrador do MySQL [root]: ").strip() or "root"
    servidor = dict(host=dados["host"], port=dados["port"], user=admin, password=getpass("Senha administrativa do MySQL: "))
    with abrir(servidor) as conexao, conexao.cursor() as cur:
        cur.execute("SELECT 1 FROM mysql.user WHERE User='unifica_app' AND Host='localhost'")
        if cur.fetchone():
            with abrir({k:v for k,v in dados.items() if k != "database"}):
                pass
        else:
            cur.execute("CREATE USER 'unifica_app'@'localhost' IDENTIFIED BY %s", (dados["password"],))
        cur.execute("CREATE DATABASE IF NOT EXISTS UNIFICA CHARACTER SET utf8mb4")
        cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, REFERENCES ON UNIFICA.* TO 'unifica_app'@'localhost'")
    with abrir(dados):
        pass
    armazenar(json.dumps(dados))
    configuracao.cache_clear()


def instalar():
    preparar_tls()
    if ambiente() or armazenar():
        with abrir(configuracao()):
            pass
    else:
        escolha = input("MySQL: [1] usar banco existente ou [2] preparar UNIFICA local [1]: ").strip()
        if escolha == "2":
            criar_base()
        elif escolha in ("", "1"):
            configurar()
        else:
            raise ConfiguracaoErro("Escolha 1 ou 2.")
    return subprocess.call([sys.executable, str(ROOT / "app.py")], cwd=ROOT)


if __name__ == "__main__":
    try:
        sys.exit(instalar())
    except Error as erro:
        sys.exit(diagnostico(erro))
    except (ConfiguracaoErro, OSError, subprocess.SubprocessError) as erro:
        sys.exit(f"Instalação interrompida: {erro}. Consulte o README e repita o comando.")
    except (KeyboardInterrupt, EOFError):
        sys.exit("Instalação interrompida.")
