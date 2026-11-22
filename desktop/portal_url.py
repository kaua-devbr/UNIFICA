"""Endereço que o UNIFICA oferece para abrir no navegador."""
from pathlib import Path
from urllib.parse import urlsplit
import warnings

LOCAL = "https://127.0.0.1:5000"
ARQUIVO = Path(__file__).resolve().parents[1] / "instance" / "portal-url.txt"


def endereco():
    try:
        url = ARQUIVO.read_text(encoding="utf-8-sig").strip()
        partes = urlsplit(url)
        if (partes.scheme == "https" and partes.hostname and partes.username is None
                and partes.password is None and partes.port != 0 and "\\" not in url
                and not any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url)):
            return url
        raise ValueError
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        warnings.warn("Confira a URL HTTPS em instance/portal-url.txt. Usando o portal local.")
    return LOCAL
