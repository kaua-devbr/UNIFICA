# UNIFICA · Portal do Aluno

Execute na pasta que contém este README, com Python 3.10 ou mais recente:

```powershell
python app.py
```

Abra http://127.0.0.1:5000. No primeiro início, o terminal mostra a matrícula **admin** e uma senha aleatória. Guarde-a antes de fechar o terminal. Use Configurações para trocar a senha. Ctrl+C encerra o servidor. Flask, Waitress, o conector MySQL e as dependências acompanham o projeto em `vendor/`. SQLite acompanha o Python oficial para Windows.

## Demonstração para a banca

1. Entre como administrador e selecione **Cadastrar alunos** no menu. Informe matrícula, nome, e-mail, turma e senha inicial.
2. Saia e entre com a matrícula e a senha do aluno. Abra **Perfil** para conferir os dados cadastrados.
3. Abra **Biblioteca escolar** em outra aba do mesmo navegador. A Biblioteca mostra o nome e a matrícula do aluno e permite pesquisar no catálogo sem pedir outra senha.
4. Saia pela Biblioteca e atualize a aba do Portal. O acesso volta para a tela de login. A opção **Lembrar de mim** mantém o acesso por até sete dias. Sem essa opção a sessão tem limite de oito horas e usa um cookie de navegador.
5. Reinicie o programa para confirmar a persistência das contas. Calendário, notas, comunicados e catálogo usam exemplos para apresentação.

## Arquitetura de autenticação

O Portal e a Biblioteca são duas aplicações Flask montadas atrás do mesmo gateway WSGI. Uma terceira aplicação recebe a senha, verifica o hash e cria uma sessão central. A cada solicitação protegida, o gateway valida o identificador dessa sessão no banco, consulta o perfil do usuário e entrega a identidade à aplicação por uma variável interna do WSGI. Somente o gateway fica exposto em 127.0.0.1. Esse modelo de SSO centralizado atende aos serviços locais sob a mesma origem. Uma integração com sistemas externos via OpenID Connect exigiria um provedor compatível com esse protocolo.

## Banco SQL

Para executar imediatamente, o programa cria `instance/unifica.sqlite3` e a chave local em `instance/secret.key`. Guarde a pasta `instance` para preservar os dados. Senhas são armazenadas como hashes com salt. O logout e a troca de senha revogam a sessão no servidor.

Para usar o **MySQL** do colégio, escolha um banco já criado e uma conta autorizada a criar tabelas e a ler e gravar dados nele. Configure no ambiente `UNIFICA_DB=mysql`, `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_DATABASE`. Os opcionais `MYSQL_HOST` e `MYSQL_PORT` têm valores padrão localhost e 3306. Essas variáveis podem ser salvas no ambiente do usuário no Windows. O comando de execução continua sendo `python app.py`. A aplicação cria as tabelas `unifica_contas` e `unifica_sessoes` no banco selecionado. Uma falha de conexão interrompe o início para evitar gravar alunos em outro banco por engano.

Cada banco tem suas próprias contas. A versão reconstruída inicia um cadastro próprio. Alunos e identidades da instalação anterior exigem migração para essas tabelas.

## Organização

- `app.py` monta os serviços, prepara o banco e inicia o servidor.
- `auth/` contém a autenticação centralizada, a troca de senha e o gateway.
- `database/` contém as operações SQL.
- `portal/`, `templates/` e `static/` mantêm as páginas e o visual do portal.
- `tests/test_sso.py` verifica cadastro, acesso aos dois serviços, autorização, persistência, troca de senha e saída. Rode `python tests/test_sso.py` com o SQLite padrão. Para testar com MySQL, use exclusivamente um banco de teste vazio.

