"""Cliente local do portal. Cada janela mantém sua própria sessão SSO."""
from html.parser import HTMLParser
from pathlib import Path
import sys

import httpx


class ErroPortal(Exception):
    pass


class SessaoExpirada(ErroPortal):
    pass


class CampoCSRF(HTMLParser):
    valor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name") == "csrf":
            self.valor = attrs.get("value")


class Cliente:
    def __init__(self, transport=None):
        self.tentar_portal_local = transport is None
        self.http = self.abrir_cliente(transport)
        self.token = None

    @staticmethod
    def abrir_cliente(transport):
        return httpx.Client(base_url="http://127.0.0.1:5000", trust_env=False,
                                 follow_redirects=False, timeout=10, transport=transport)

    def conectar_localmente(self):
        raiz = str(Path(__file__).resolve().parents[1])
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        from app import create_app
        from mysql.connector import Error

        try:
            portal = create_app()
        except KeyError as erro:
            if erro.args[0] not in ("MYSQL_USER", "MYSQL_PASSWORD"):
                raise
            raise ErroPortal(f"Configure {erro.args[0]} no terminal que inicia o Flet.") from erro
        except Error as erro:
            raise ErroPortal(f"O portal local falhou ao acessar o MySQL (erro {erro.errno}). Confira o serviço e a configuração do banco.") from erro
        self.http.close()
        self.http = self.abrir_cliente(httpx.WSGITransport(app=portal))
        self.tentar_portal_local = False

    def requisitar(self, metodo, caminho, **opcoes):
        try:
            return self.http.request(metodo,caminho,**opcoes)
        except httpx.ConnectError as err:
            if self.tentar_portal_local and (metodo, caminho) == ("GET", "/sso/login"):
                self.conectar_localmente()
                return self.http.request(metodo, caminho, **opcoes)
            raise ErroPortal("A conexão com o portal foi interrompida. Entre novamente.") from err
        except httpx.RequestError as err:
            raise ErroPortal("Não foi possível acessar o portal. Inicie python app.py na pasta UNIFICA.") from err

    def csrf_sso(self, caminho):
        r = self.requisitar("GET",caminho)
        if r.is_redirect:
            raise SessaoExpirada("Entre novamente no portal.")
        campo = CampoCSRF()
        campo.feed(r.text)
        if not r.is_success or not campo.valor:
            raise ErroPortal("O serviço de identidade está indisponível.")
        return campo.valor

    def login(self, matricula, senha):
        r = self.requisitar("POST","/sso/login",data={"csrf":self.csrf_sso("/sso/login"),
                            "matricula":matricula,"senha":senha,"destino":"/inicio"})
        if r.status_code==200:
            return None
        if r.status_code!=303:
            raise ErroPortal("O serviço de identidade recusou a solicitação.")
        return self.conta()

    def api(self,caminho,dados=None):
        if dados is None:
            r = self.requisitar("GET","/desktop/api/"+caminho)
        else:
            r = self.requisitar("POST","/desktop/api/"+caminho,data=dict(dados,form_token=self.token))
        if r.is_redirect or r.status_code==401:
            self.token = None
            raise SessaoExpirada("Sua sessão terminou. Entre novamente.")
        if r.status_code==403:
            raise ErroPortal("Esta ação requer uma conta de administrador.")
        if not r.is_success:
            detalhe = r.json().get("erro") if "application/json" in r.headers.get("content-type","") else None
            raise ErroPortal(detalhe or "O portal não concluiu a operação.")
        return r.json()

    def conta(self):
        dados = self.api("conta")
        self.token = dados.pop("form_token")
        return dados

    def sair(self):
        try:
            r = self.requisitar("POST","/sair",data={"form_token":self.token})
            if not r.is_redirect:
                raise ErroPortal("Não foi possível encerrar a sessão.")
        finally:
            self.http.cookies.clear()
            self.token = None

    def alterar_senha(self, atual, nova):
        r = self.requisitar("POST","/sso/senha",data={"atual":atual,"nova":nova,
                            "csrf":self.csrf_sso("/sso/senha")})
        if r.status_code==200:
            raise ErroPortal("Confira a senha atual e use de 8 a 256 caracteres na nova senha.")
        if r.status_code!=303:
            raise ErroPortal("Não foi possível atualizar a senha.")
        self.http.cookies.clear()
        self.token=None

