# rpa_web

Automação RPA (Robotic Process Automation) que faz login em um sistema web e executa tarefas usando `pyautogui` (cliques e digitação automáticos) em uma janela anônima do Chrome.

## Visão geral

- **Objetivo**: abrir o site alvo, fazer login (usuário e senha) e executar sequências de cliques (ex.: botões pós-login).
- **Automação**: baseada em coordenadas da tela (x, y) definidas no arquivo `.env`. Usuário e senha são **colados** (Ctrl+V) para suportar e-mail e caracteres especiais.
- **Navegador**: Google Chrome em modo **anônimo** (`--incognito`).
- **Datas inválidas**: o script **não executa** em datas listadas em `data_invalidas.txt` (ex.: feriados nacionais e estaduais do RJ).

## Pré-requisitos

- **Sistema**: Windows
- **Python**: 3.13+ (gerenciado pelo `uv`)
- **Ferramentas**:
  - [uv](https://docs.astral.sh/uv/)
  - Google Chrome instalado

## Configuração

### 1. Variáveis de ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto (se ainda não existir) com, por exemplo:

```env
USERNAME=seu_usuario_ou_email
PASSWORD=sua_senha
SITE=https://seu-site-alvo.com/

# Posições do campo inicial (formato "(x, y)" ou "x=553, y=405")
EMAIL_FIELD="(553, 405)"

# Botões após o login (ajuste conforme o fluxo do seu sistema)
BUTTON1="(1170, 177)"
BUTTON2="(686, 428)"
```

- **`USERNAME` / `PASSWORD`**: credenciais de login (e-mail e senha com caracteres especiais são suportados via cola).
- **`SITE`**: URL da página de login.
- **`EMAIL_FIELD`**: coordenadas para clicar no campo e iniciar login.
- **`BUTTON1`, `BUTTON2`, `FECHAR_WINDOW`**: coordenadas para ações após o login (ex.: ação 1, confirmar, fechar janela).

> **Importante**: o arquivo `.env` contém senha. Não envie esse arquivo para o Git / repositórios remotos.

### 2. Datas em que o script não executa (`data_invalidas.txt`)

O arquivo `data_invalidas.txt` na raiz do projeto define em quais datas a automação **não** deve rodar (ex.: feriados). O script verifica a data de hoje antes de iniciar; se estiver na lista, encerra sem abrir o navegador.

- **Formato**: uma data por linha, em `DD/MM` (recorrente, todo ano) ou `DD/MM/AAAA` (data específica).
- **Comentários**: linhas que começam com `#` ou texto após a data (ex.: `01/01 - Confraternização`) são ignorados.
- O arquivo já vem preenchido com **feriados nacionais** e **feriados estaduais do Rio de Janeiro**. Feriados móveis (Carnaval, Sexta-feira Santa, Corpus Christi) estão com datas de 2026; para outros anos, basta acrescentar novas linhas.

Exemplo de linhas válidas:

```
01/01 - Confraternização Universal
23/04 - Dia de São Jorge (RJ)
04/06/2026 - Corpus Christi
```

### 3. Descobrir as coordenadas dos elementos

Use o script `auxiliar.py` para descobrir a posição do mouse na tela:

```bash
uv run auxiliar.py
```

- Você terá **5 segundos** para posicionar o mouse sobre o campo/botão desejado.
- Após isso, o script imprime algo como `Point(x=553, y=405)` no terminal.
- Use esses valores no `.env` em `EMAIL_FIELD`, `PASSWORD_FIELD`, `LOGIN_BUTTON`, `BUTTON1`, `BUTTON2`, etc.

## Como o script funciona

O `main.py` executa, em sequência:

1. **Verifica a data de hoje** em `data_invalidas.txt`. Se estiver na lista, exibe uma mensagem e encerra sem executar a automação.
2. Carrega o `.env` com `load_dotenv(override=True)` (no Windows, isso evita que `USERNAME` do sistema sobrescreva o do `.env`).
3. Lê credenciais, `SITE` e coordenadas (formato `"(x, y)"` ou `"x=553, y=405"`).
4. Abre o Chrome em modo anônimo na URL configurada e espera a página carregar (~5 s).
5. Clica no campo de e-mail, **cola** o usuário (Ctrl+V). Clica no campo de senha, **cola** a senha. Clica no botão de login.
6. Após o login: clica em `BUTTON1`, depois `BUTTON2`, depois em `FECHAR_WINDOW` (fechar janela).

Usuário e senha são colados via clipboard (`pyperclip` + Ctrl+V) para funcionar com e-mail e caracteres especiais (`@`, `+`, `?`, etc.).

## Como rodar o projeto

Após clonar o repositório:

```bash
uv sync          # instala as dependências (pyautogui, pyperclip, python-dotenv, etc.)
uv run main.py   # executa a automação de login
```

Se estiver em PowerShell e o uv mostrar o aviso de hardlink, veja a seção de troubleshooting abaixo.

## Comandos básicos do uv

### Ambiente virtual e dependências

```bash
# Criar ambiente virtual (se ainda não existir)
uv venv

# Ativar o ambiente (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Instalar dependências do projeto
uv sync

# Adicionar uma dependência
uv add <pacote>

# Adicionar dependência de desenvolvimento
uv add --dev <pacote>

# Remover uma dependência
uv remove <pacote>
```

### Executar o projeto com uv

```bash
uv run main.py
```

### Outros comandos úteis

```bash
# Atualizar dependências
uv lock --upgrade

# Listar dependências instaladas
uv pip list

# Compilar requirements.txt (se precisar)
uv pip compile pyproject.toml -o requirements.txt
```

## Troubleshooting

### Aviso "Failed to hardlink files" no Windows

Se aparecer o aviso de que o uv não conseguiu usar hardlinks e está fazendo cópia completa (comum quando o cache e o projeto estão em discos/partições diferentes), você pode suprimir o aviso e usar modo cópia:

**Na sessão atual (PowerShell):**
```powershell
$env:UV_LINK_MODE = "copy"
uv run main.py
```

**Sempre que rodar (uma vez por terminal):**
```powershell
$env:UV_LINK_MODE = "copy"
```

**Ou em cada comando:**
```powershell
uv run --link-mode=copy main.py
```

Para tornar permanente no seu usuário: **Configurações do Windows** → **Variáveis de ambiente** → adicione `UV_LINK_MODE` = `copy`.
