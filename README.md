# UNIFICA — Um login para o ambiente escolar

O UNIFICA reúne o portal escolar e o aplicativo Flet. O administrador gerencia usuários, turmas, professores, notas, frequência, eventos e comunicados. O aluno acessa sua área acadêmica. As duas interfaces usam os mesmos dados no MySQL.

## Instalação rápida e inicialização

Com Python 3 e o MySQL Server já instalado e em execução, abra o terminal na pasta de `app.py`. No Windows, execute **`python instalar.py`**. No Ubuntu/Debian ou macOS, use **`python3 instalar.py`**. Use um terminal interativo. O instalador prepara o HTTPS com mkcert, registra uma autoridade certificadora local para o navegador, testa o MySQL e inicia o portal. O sistema pode pedir autorização para instalar o certificado ou pacotes. No Windows é necessário winget ou mkcert no PATH. No Ubuntu/Debian use uma sessão gráfica com chaveiro desbloqueado. No macOS, prepare o pacote keyring conforme o passo 4.

Se já configurou o MySQL, o instalador reutiliza a conexão. Caso contrário, escolha **1** para conectar ao banco que contém seus cadastros ou **2** para preparar o banco local UNIFICA e a conta unifica_app. Na opção 2, informe a senha da conta MySQL da aplicação e, separadamente, a credencial administrativa para criar a base e conceder acesso. O portal cria suas tabelas ao iniciar. Se a conta unifica_app já existir, use a senha atual dela.

No Windows, você também pode dar dois cliques em **Abrir-UNIFICA.cmd** para instalar na primeira vez ou iniciar o portal nas próximas. Nas próximas vezes, execute **`python app.py`** (ou `python3 app.py`). O terminal exibe o login admin, a senha local e, na linha seguinte, **https://127.0.0.1:5000**. Clique no endereço conforme o terminal ou copie para o navegador. No primeiro uso de uma conta existente, confirme a senha do portal para ativar o lembrete. O endereço é local ao computador. Para renovar os certificados, encerre o portal e repita o instalador. Mantenha a chave privada do mkcert e a pasta instance somente no seu computador.

Os passos abaixo detalham a preparação manual do MySQL, o suporte e a instalação opcional do Flet. Mesmo ao preparar o banco pelo Workbench, execute o instalador uma vez para habilitar o HTTPS.

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

## 4. Inicie o portal e salve a conexão

Na pasta que contém `app.py`, execute o comando do seu sistema. No Linux com sessão gráfica, instale primeiro o utilitário que acessa o cofre de senhas. No Ubuntu/Debian, use `sudo apt install libsecret-tools`. No Fedora, use `sudo dnf install libsecret`. No macOS, use um ambiente virtual com `python3 -m pip install keyring` e execute o portal com esse mesmo Python. No Windows, o projeto usa a proteção de dados da própria conta do Windows.

| Sistema | Iniciar o site | Testar e regravar a configuração |
| --- | --- | --- |
| Windows | `python app.py` | `python app.py --configurar-banco` |
| Linux ou macOS | `python3 app.py` | `python3 app.py --configurar-banco` |

No primeiro acesso pelo terminal, pressione Enter para aceitar cada sugestão ou digite o valor da sua instalação. Os valores sugeridos são servidor `127.0.0.1`, porta `3306`, banco `UNIFICA` e usuário `unifica_app`. Para aproveitar uma base existente, informe o nome exato dela, por exemplo `unifica_demo`. Por fim, digite a senha desse usuário do **MySQL**. O programa testa a conexão antes de salvar os dados para sua conta do sistema operacional. Cada computador tem sua própria configuração.

Abra https://127.0.0.1:5000 quando o terminal indicar que o portal está disponível. Em uma base nova, use a matrícula **admin** e a senha de primeiro acesso exibida no terminal. Em uma base existente, use a senha atual do portal. Mantenha o terminal aberto enquanto usa o site. Após reiniciar o computador, basta repetir o comando de iniciar o site.

## 5. Confira o acesso

Entre como administrador e cadastre um aluno de teste. Saia da conta e entre com a matrícula desse aluno. Confira se o perfil e a turma correspondem ao cadastro e se o menu mostra a área do aluno.

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

## Suporte

Execute os comandos a partir da pasta que contém `app.py`.

| Mensagem ou situação | Comando de suporte ou ação |
| --- | --- |
| Alterei a senha, o nome do banco ou o servidor | Execute `python app.py --configurar-banco` no Windows ou `python3 app.py --configurar-banco` no Linux/macOS. Reinicie o portal e o Flet para usar os novos dados. |
| Variáveis de uma instalação anterior | No Bash, use `unset MYSQL_HOST MYSQL_PORT MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD`. No PowerShell, use `'MYSQL_HOST','MYSQL_PORT','MYSQL_DATABASE','MYSQL_USER','MYSQL_PASSWORD' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }`. Se elas voltarem no próximo terminal, revise o perfil de inicialização. |
| Cofre indisponível no Linux | Execute `command -v secret-tool`. No Ubuntu/Debian, instale com `sudo apt install libsecret-tools gnome-keyring` e desbloqueie o chaveiro da sua sessão gráfica. Em SSH ou em um servidor sem chaveiro, use o bloco Bash abaixo. |
| Cofre indisponível no macOS | No ambiente Python do portal, execute `python3 -m pip install keyring` e desbloqueie o chaveiro de início de sessão. Para iniciar o portal dentro do Flet, instale também no ambiente do aplicativo com `.venv/bin/python -m pip install keyring`. |
| Erros 1044, 1045 ou 1142 | Teste com `mysql -h 127.0.0.1 -P 3306 -u unifica_app -p UNIFICA`. Use a senha do MySQL. Confira as permissões do passo 3 e reconfigure a conexão se necessário. |
| Erro 1049, banco desconhecido | Execute `mysql -u root -p -e "SHOW DATABASES;"`. Se o banco existe, configure o nome exato. Para criar uma nova instalação, siga o passo 3. |
| Erro 2003, conexão recusada | No Ubuntu/Debian, confira `systemctl status mysql` e, se parado, execute `sudo systemctl start mysql`. No Windows, descubra o serviço com `Get-Service *mysql*` e, em PowerShell administrativo, use por exemplo `Start-Service MySQL84` se esse for o nome listado. |
| Flet abre, mas o portal não responde | Inicie o site pelo passo 4 e abra https://127.0.0.1:5000/healthz no navegador. O resultado esperado é `{"status":"ok"}`. Depois execute a última linha do passo 6 em outro terminal. O Flet também pode iniciar o portal internamente quando a configuração já está salva. |
| Aparece `KeyError: 'MYSQL_USER'` ou `DispatcherMiddleware is not defined` | Confira a versão com `python app.py --help` (Linux/macOS: `python3 app.py --help`). Esta edição lista `--configurar-banco` e inclui a importação em `auth/gateway.py`. Se a opção faltar, extraia o ZIP atualizado numa pasta nova e execute a partir dela. |
| Porta 5000 ocupada | Abra https://127.0.0.1:5000/healthz para verificar se o portal já está ativo. Para trocar de versão, encerre o portal anterior no terminal com Ctrl+C. |

### Alternativa no Linux sem cofre ou sessão gráfica

O portal aceita as credenciais do ambiente. Use este bloco no Bash para uma execução temporária. Ajuste o banco e o usuário à sua instalação. Com o site aberto, o Flet pode se conectar ao portal por HTTP em outro terminal.

```bash
export MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306
export MYSQL_DATABASE=UNIFICA MYSQL_USER=unifica_app
IFS= read -rs -p 'Senha de unifica_app no MySQL: ' MYSQL_PASSWORD
echo
export MYSQL_PASSWORD
python3 app.py
```

No Windows, para executar temporariamente sem o cofre, use o PowerShell:

```powershell
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3306'
$env:MYSQL_DATABASE = 'UNIFICA'
$env:MYSQL_USER = 'unifica_app'
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new('', (Read-Host 'Senha do MySQL' -AsSecureString)).Password
python app.py
```

### Falhas durante o uso

Em caso de falha de conexão durante um cadastro, reabra a lista e confira se o registro foi salvo antes de enviar novamente. O terminal do portal mostra o código MySQL das falhas tratadas. Para testar a conexão a partir da máquina do portal, execute:

```sh
mysql -h 127.0.0.1 -P 3306 -u unifica_app -p UNIFICA -e "SELECT DATABASE(), CURRENT_USER(); SHOW TABLES;"
```

Use o nome do seu banco e a porta configurada. Para 1054 ou 1146, confira a estrutura no Workbench com `SHOW CREATE TABLE nome_da_tabela;` e compare com o SQL da mesma versão do projeto. Faça backup antes de alterar uma tabela existente. Para 1205 ou 1213, atualize a tela e confira o estado da operação antes de tentar novamente.

### Ver a senha do administrador ao iniciar

Execute `python app.py` (Linux/macOS: `python3 app.py`) em um terminal local. Na primeira execução com uma conta admin já existente, pressione Enter e informe a senha atual do portal para guardá-la no cofre. Se esqueceu a senha, a opção R permite redefini-la após confirmação e encerra as sessões da conta. Nas próximas execuções, o terminal mostra a matrícula admin e a senha conferida com o banco. Quem consegue ver esse terminal consegue ler a senha.

A alteração de senha pelo formulário da própria conta também atualiza o lembrete local depois da gravação no MySQL. Em outro computador ou após uma troca externa, informe a senha atual uma vez. No Linux o recurso usa secret-tool e um chaveiro desbloqueado. No macOS usa o pacote keyring e o Chaves. No Windows usa a proteção da conta do Windows.

### Abrir o portal no navegador

Com o servidor iniciado, clique em **Abrir portal** abaixo de LOGIN no Flet ou abra a URL exibida pelo terminal. O endereço padrão é `https://127.0.0.1:5000`. Para usar seu servidor publicado, salve a URL HTTPS completa como única linha em `instance/portal-url.txt` na pasta do projeto e reinicie o portal e o aplicativo. O arquivo configura o link do navegador. A publicação e o certificado HTTPS são configurados no servidor.

