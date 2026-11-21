# UNIFICA · Portal do Aluno

O projeto usa **MySQL**. Antes de iniciar, crie um banco chamado `UNIFICA` (ou outro nome) e configure no PowerShell:

```powershell
$env:MYSQL_USER = "seu_usuario"
$env:MYSQL_PASSWORD = "sua_senha"
$env:MYSQL_DATABASE = "UNIFICA"
```

Depois execute na pasta que contém este README, com Python 3.10 ou mais recente:

```powershell
python app.py
```

Abra http://127.0.0.1:5000. No primeiro início, o terminal mostra a matrícula **admin** e uma senha aleatória. Guarde-a antes de fechar o terminal. Use Configurações para trocar a senha. Ctrl+C encerra o servidor. Flask, Waitress, o conector MySQL e as dependências acompanham o projeto em `vendor/`.

## Demonstração para a banca

1. Entre como administrador e selecione **Cadastrar alunos** no menu. Informe matrícula, nome, e-mail, turma e senha inicial.
2. Saia e entre com a matrícula e a senha do aluno. Abra **Perfil** para conferir os dados cadastrados.
3. Abra **Biblioteca escolar** em outra aba do mesmo navegador. A Biblioteca mostra o nome e a matrícula do aluno e permite pesquisar no catálogo sem pedir outra senha.
4. Saia pela Biblioteca e atualize a aba do Portal. O acesso volta para a tela de login. A opção **Lembrar de mim** mantém o acesso por até sete dias. Sem essa opção a sessão tem limite de oito horas e usa um cookie de navegador.
5. Reinicie o programa para confirmar a persistência das contas. Calendário, notas, comunicados e catálogo usam exemplos para apresentação.

## Arquitetura de autenticação

O Portal e a Biblioteca são duas aplicações Flask montadas atrás do mesmo gateway WSGI. Uma terceira aplicação recebe a senha, verifica o hash e cria uma sessão central. A cada solicitação protegida, o gateway valida o identificador dessa sessão no banco, consulta o perfil do usuário e entrega a identidade à aplicação por uma variável interna do WSGI. Somente o gateway fica exposto em 127.0.0.1. Esse modelo de SSO centralizado atende aos serviços locais sob a mesma origem. Uma integração com sistemas externos via OpenID Connect exigiria um provedor compatível com esse protocolo.

## Banco de dados (MySQL)

O banco escolhido já precisa existir, e a conta informada precisa poder criar tabelas e ler e gravar dados nele. Configure `MYSQL_USER`, `MYSQL_PASSWORD` e, se quiser outro nome de banco, `MYSQL_DATABASE`. Os opcionais `MYSQL_HOST` e `MYSQL_PORT` têm valores padrão localhost e 3306. A aplicação cria as tabelas `unifica_contas` e `unifica_sessoes` no banco selecionado. Uma falha de conexão interrompe o início. A chave local fica em `instance/secret.key`; guarde a pasta `instance`. Senhas são armazenadas como hashes com salt. O logout e a troca de senha revogam a sessão no servidor.

O CRUD de alunos está em `database/crud.py` (cadastrar, listar, buscar, atualizar e deletar) e é usado pela página **Cadastrar alunos** do administrador. A conexão usada por ele e pelo login é a mesma, a função `conectar()` de `database/store.py`.

## Organização

- `app.py` reúne as rotas do Portal, o cadastro de alunos e a inicialização dos serviços. Por exemplo, a rota /perfil chama perfil() e exibe templates/perfil.html.
- `auth/` contém a autenticação centralizada, a troca de senha e o gateway.
- `database/` contém a conexão com o MySQL (`store.py`) e o CRUD de alunos (`crud.py`).
- `templates/` guarda as páginas HTML e `static/` reúne CSS e imagens.
- `dados_demo.py` contém os exemplos de notas, eventos e comunicados.
- `requirements.txt` lista as versões incluídas em `vendor/`.
- `tests/test_sso.py` verifica cadastro, acesso aos dois serviços, autorização, persistência, troca de senha e saída. Rode `python tests/test_sso.py` com as variáveis do MySQL configuradas, usando exclusivamente um banco de teste vazio.

