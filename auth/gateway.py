import hashlib
import time
from flask import redirect, request, session
from werkzeug.middleware.dispatcher import DispatcherMiddleware


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
            rows = self.store.query("""SELECT c.matricula,c.nome,c.email,c.turma,c.papel
                FROM unifica_sessoes s JOIN unifica_contas c ON c.matricula=s.matricula
                LEFT JOIN unifica_perfis p ON p.matricula=c.matricula
                WHERE s.token=? AND s.expira>? AND COALESCE(p.ativo,1)=1""", (digest(token), int(time.time())), rows=True) if token else []
            if not rows:
                from urllib.parse import urlencode
                dest = request.full_path.rstrip("?") if request.method == "GET" else "/"
                return redirect("/sso/login?" + urlencode({"destino": dest}))(environ, start_response)
            environ["unifica.account"] = rows[0]
            environ["unifica.session"] = digest(token)
        return self.services(environ, start_response)

