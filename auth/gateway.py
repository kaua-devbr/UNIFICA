import hashlib
import time
import logging
from mysql.connector import Error as MySQLError
from werkzeug.wrappers import Response
from flask import redirect, request, session
from werkzeug.middleware.dispatcher import DispatcherMiddleware


def erro_banco(erro):
    logging.getLogger(__name__).error("Falha de banco no UNIFICA (MySQL %s)", erro.errno)
    if erro.errno in (1062, 1451, 1452):
        mensagem, status = "Conflito de cadastro. Confira os dados e os registros relacionados.", 409
    elif erro.errno in (1040, 1205, 1213, 2002, 2003, 2005, 2006, 2013, 2055):
        mensagem, status = "Banco temporariamente indisponível. Atualize a consulta e confira o registro antes de repetir uma alteração.", 503
    else:
        mensagem, status = "Falha ao acessar o banco. Consulte o código MySQL no terminal do portal.", 500
    if request.path.startswith("/desktop/api/"):
        import json
        return Response(json.dumps({"erro": mensagem}), status=status, mimetype="application/json")
    return Response(mensagem, status=status, mimetype="text/plain")


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Gateway:
    """Authenticate at one entry point, then pass trusted WSGI identity to a service."""
    def __init__(self, identity, portal, library, store):
        self.identity = identity
        self.store = store
        self.services = DispatcherMiddleware(portal, {"/biblioteca": library})

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "/")
        if path.startswith("/sso/"):
            return self.identity(environ, start_response)
        if path.startswith("/static/") or path == "/healthz":
            return self.services(environ, start_response)
        with self.identity.request_context(environ):
            token = session.get("token")
            try:
                rows = self.store.query("""SELECT c.matricula,c.nome,c.email,c.turma,c.papel
                FROM unifica_sessoes s JOIN unifica_contas c ON c.matricula=s.matricula
                LEFT JOIN unifica_perfis p ON p.matricula=c.matricula
                WHERE s.token=? AND s.expira>? AND COALESCE(p.ativo,1)=1""", (digest(token), int(time.time())), rows=True) if token else []
            except MySQLError as erro:
                return erro_banco(erro)(environ, start_response)
            if not rows:
                from urllib.parse import urlencode
                dest = request.full_path.rstrip("?") if request.method == "GET" else "/"
                return redirect("/sso/login?" + urlencode({"destino": dest}))(environ, start_response)
            environ["unifica.account"] = rows[0]
            environ["unifica.session"] = digest(token)
        return self.services(environ, start_response)


