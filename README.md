# UNIFICA · Um login para o ambiente escolar

Imagine que um aluno abriu o portal para consultar suas informações e, logo depois, quis pesquisar um livro na biblioteca. Ele já informou a matrícula e a senha. O UNIFICA permite que a biblioteca reconheça esse mesmo aluno quando ele abre uma segunda aba. Esse é o **Single Sign-On (SSO)** que o projeto demonstra.

O administrador gerencia usuários, turmas, professores, notas, frequência, eventos e comunicados. O aluno acessa sua área acadêmica. Na edição completa, o aplicativo Flet oferece outra interface para os dados do portal. O site e o aplicativo utilizam o mesmo MySQL. O Flet abre sua própria sessão, enquanto o portal e a biblioteca compartilham o login do navegador.

## 1. Prepare o computador

O roteiro usa Python 3.13, MySQL Community Server 8.4 e um navegador. Para o site, Flask, Waitress e o conector do banco já acompanham o projeto em `vendor/`.

1. Instale o Python. No Windows, verifique a instalação em um novo PowerShell com `py -3.13 --version`. No macOS ou Linux, use `python3 --version`. Se o seu Windows reconhece `python` no lugar de `py -3.13`, use `python` nos comandos deste guia. [Downloads do Python](https://www.python.org/downloads/)
2. Instale o MySQL Server para o seu sistema. No Windows, conclua a configuração pelo MySQL Configurator. No macOS ou Linux, siga as instruções do pacote correspondente ao sistema. Inicie o serviço, mantenha a porta 3306 e guarde a credencial administrativa. [Downloads do MySQL Server](https://dev.mysql.com/downloads/mysql/) · [Guia de instalação](https://dev.mysql.com/doc/refman/8.4/en/installing.html)
3. Para executar o SQL com interface gráfica, instale também o MySQL Workbench. Se preferir o terminal, use o cliente `mysql`. [Downloads do Workbench](https://dev.mysql.com/downloads/workbench/)

## 2. Abra a pasta do projeto

Baixe o ZIP do repositório e extraia seu conteúdo ou use Git:

```sh
git clone https://github.com/kaua-devbr/UNIFICA.git
cd UNIFICA
```

Abra o terminal na pasta que contém `app.py`, `vendor/` e `database/criar_banco.sql`. Para testar o Flet, confira se a mesma cópia inclui `desktop/main.py` e `desktop/requirements.txt`. Se a versão baixada contiver apenas o portal, obtenha a edição completa para a etapa do aplicativo. [Repositório do projeto](https://github.com/kaua-devbr/UNIFICA)

## 3. Crie o banco de dados

**Se já usa o UNIFICA**, mantenha o nome e as credenciais do banco que contém seus cadastros e vá para o passo 4. Em outro computador, o script cria uma base nova. Para levar os dados existentes, restaure uma exportação do banco original.

**Pelo Workbench**, conecte-se ao servidor local como administrador do MySQL. Abra **File → Open SQL Script**, selecione `database/criar_banco.sql` e execute o script inteiro pelo botão de raio. Ao final, `SHOW TABLES` deve listar, entre outras, `unifica_contas` e `unifica_sessoes` no banco `UNIFICA`.

**Pelo terminal**, na pasta do projeto, execute `mysql -u root -p`. Digite a senha administrativa do MySQL. Quando aparecer `mysql>`, execute:

```sql
SOURCE database/criar_banco.sql;
```

Na mesma conexão administrativa, crie uma conta para o aplicativo. Substitua a senha de exemplo por uma sua e guarde-a para o passo seguinte. Execute uma vez:

```sql
CREATE USER 'unifica_app'@'localhost' IDENTIFIED BY 'Troque_por_uma_senha_sua!';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, REFERENCES
ON UNIFICA.* TO 'unifica_app'@'localhost';
```

## 4. Inicie o portal

Execute o bloco do seu sistema no terminal, dentro da pasta de `app.py`. A senha solicitada aqui pertence ao usuário **unifica_app do MySQL**. Se o banco existente se chama `unifica_demo`, ajuste `MYSQL_DATABASE` e informe as credenciais que já usa com ele.

### Windows · PowerShell

```powershell
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3306'
$env:MYSQL_DATABASE = 'UNIFICA'
$env:MYSQL_USER = 'unifica_app'
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new('', (Read-Host 'Senha do usuário MySQL' -AsSecureString)).Password
py -3.13 .\app.py
```

### macOS e Linux · Bash

```bash
export MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306
export MYSQL_DATABASE=UNIFICA MYSQL_USER=unifica_app
read -rsp 'Senha do usuário MySQL: ' MYSQL_PASSWORD
echo
export MYSQL_PASSWORD
python3 app.py
```

Com um banco novo, o terminal mostra a matrícula **admin** e a senha gerada para o primeiro acesso. Guarde essa senha e entre no [portal local](http://127.0.0.1:5000). Em uma instalação existente, use a senha atual do administrador. Se sua edição do Windows mostrar opções para guardar ou redefinir a senha do portal, siga as instruções do terminal.

Mantenha o terminal aberto durante o uso. **Ctrl+C** encerra o servidor. Para reiniciar no mesmo terminal, repita apenas o comando que executa `app.py`. Em um terminal novo, configure as variáveis novamente se o seu ambiente ainda não as carregar automaticamente. Os cadastros ficam no MySQL.

## 5. Demonstre o SSO

| Etapa | O que fazer | Resultado esperado |
| --- | --- | --- |
| 1 | Entre como admin e cadastre um aluno fictício, por exemplo `teste001`, com turma e senha inicial de pelo menos oito caracteres. | O aluno aparece na lista do administrador. |
| 2 | Saia da conta administrativa e entre no portal com a matrícula e a senha do aluno. Abra **Perfil**. | O perfil mostra os dados cadastrados. |
| 3 | Sem fechar o portal, abra a [Biblioteca Escolar](http://127.0.0.1:5000/biblioteca/) em outra aba do mesmo navegador. Pesquise “Machado”. | A biblioteca reconhece o aluno sem pedir outra senha e exibe o resultado da pesquisa. |
| 4 | Na biblioteca, escolha **Sair da conta**, confirme a saída de todos os serviços e atualize a aba do portal. | O portal pede login novamente. |

Use `127.0.0.1` nas duas abas e mantenha o mesmo perfil do navegador. Uma janela anônima e uma janela comum têm cookies separados.

## 6. Abra o aplicativo Flet

Com o portal da **edição completa** em execução, abra um segundo terminal na mesma pasta do projeto. Crie um ambiente virtual e instale as dependências do aplicativo.

**Windows · PowerShell**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\desktop\requirements.txt
.\.venv\Scripts\python.exe .\desktop\main.py
```

**macOS ou Linux · terminal com ambiente gráfico**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r desktop/requirements.txt
.venv/bin/python desktop/main.py
```

Nas próximas execuções, use apenas a última linha. Para conferir o compartilhamento dos dados, entre no Flet como administrador, cadastre um professor fictício de História e atualize **Gerenciar professores** no site. Depois, altere a matéria no site e reabra a lista no Flet. O mesmo professor deve aparecer com a matéria atualizada nas duas interfaces.

## Como o projeto está organizado

- `app.py` inicia os serviços locais na porta 5000.
- `auth/` verifica a senha e consulta a sessão central antes de liberar os serviços protegidos. O banco guarda hashes das senhas. A chave de assinatura local fica em `instance/secret.key`.
- `database/` contém o script SQL, a conexão e as operações de leitura e gravação.
- `portal/`, `templates/` e `static/` reúnem a lógica e as telas do site.
- `desktop/` contém o cliente e as telas do Flet na edição completa.

## Se algo der errado

| Sintoma | Como resolver |
| --- | --- |
| `KeyError: 'MYSQL_USER'` ou `'MYSQL_PASSWORD'` | Execute o passo 4 no mesmo terminal que vai iniciar `app.py`. |
| `1049 Unknown database` | Confira o valor de `MYSQL_DATABASE` e se o banco aparece no Workbench. O script cria `UNIFICA`. |
| `1045 Access denied` | Teste a credencial do MySQL no Workbench e confira as permissões no banco selecionado. |
| Erro 2003 ou conexão recusada | Inicie o serviço MySQL e confirme host e porta. |
| Porta 5000 ocupada | Confira se o portal já está aberto em outro terminal. Para trocar de cópia, encerre a anterior com Ctrl+C. |
| Flet abre, mas não consegue entrar | Abra o portal no navegador e confirme que ele está rodando a partir da mesma edição que contém `desktop/`. Use o Python do ambiente virtual para iniciar o Flet. |
