import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


def field(response, name):
    return re.search(fr'name="{name}"\s+value="([^"]+)"', response.get_data(as_text=True))[1]


class SingleSignOn(unittest.TestCase):
    def test_school_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                app = create_app(directory)
            secret = output.getvalue().split("senha: ")[1].strip()
            client = app.test_client()

            def login(matricula, password, destination):
                page = client.get(destination, follow_redirects=True)
                return client.post("/sso/login", data={
                    "csrf": field(page, "csrf"), "matricula": matricula,
                    "senha": password, "destino": destination}, follow_redirects=True)

            admin = login("admin", secret, "/admin/alunos")
            self.assertEqual(admin.status_code, 200)
            account = dict(matricula="2026001", nome="Aluno de Teste", turma="3B",
                           email="aluno@example.test", senha="SenhaExemplo123",
                           form_token=field(admin, "form_token"))
            saved = client.post("/admin/alunos", data=account, follow_redirects=True)
            self.assertIn("Aluno de Teste", saved.get_data(as_text=True))
            self.assertEqual(client.post("/sair").status_code, 400)
            client.post("/sair", data={"form_token": field(saved, "form_token")})
            self.assertIn("/sso/login", client.get("/biblioteca/").location)

            # A fresh application must open the same accounts and persistent signing key.
            client = create_app(directory).test_client()
            self.assertIn("incorreta", login("2026001", "incorreta", "/perfil").get_data(as_text=True))
            profile = login("2026001", account["senha"], "/perfil")
            self.assertIn(account["email"], profile.get_data(as_text=True))
            for path in ("/inicio", "/notas", "/calendario", "/comunicados", "/configuracoes"):
                self.assertEqual(client.get(path).status_code, 200, path)
            self.assertEqual(client.get("/admin/alunos").status_code, 403)
            self.assertEqual(client.post("/admin/alunos", data=account | {
                "form_token": field(profile, "form_token")}).status_code, 403)
            library = client.get("/biblioteca/?q=machado")
            self.assertEqual(library.status_code, 200)
            self.assertIn("Aluno de Teste", library.get_data(as_text=True))
            self.assertIn("Dom Casmurro", library.get_data(as_text=True))
            self.assertNotIn("O Quinze", library.get_data(as_text=True))
            change = client.get("/sso/senha")
            client.post("/sso/senha", data={"csrf": field(change,"csrf"),
                        "atual": account["senha"], "nova": "NovaSenha123"})
            self.assertIn("/sso/login", client.get("/biblioteca/").location)
            self.assertIn("incorreta", login("2026001", account["senha"], "/perfil").get_data(as_text=True))
            self.assertIn("Aluno de Teste", login("2026001", "NovaSenha123", "/biblioteca/").get_data(as_text=True))
            logout = client.get("/sso/sair")
            client.post("/sso/sair", data={"csrf": field(logout, "csrf")})
            for path in ("/perfil", "/biblioteca/"):
                self.assertIn("/sso/login", client.get(path).location)


if __name__ == "__main__":
    unittest.main()


