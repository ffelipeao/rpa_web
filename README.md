# rpa_web

Automação RPA (Robotic Process Automation) que faz login em um sistema web e executa tarefas usando **Playwright**, interagindo com os elementos da página pelos **IDs do formulário** (sem depender de coordenadas da tela).

## Visão geral

- **Objetivo**: abrir o site alvo, fazer login (usuário e senha) e executar sequências de cliques (ex.: botões pós-login).
- **Automação**: baseada nos **IDs dos elementos** (campos e botões) definidos no arquivo `.env`. O Playwright localiza os elementos pelo `id` no HTML, evitando erros quando a tela ou a resolução mudam.
- **Navegador**: Google Chrome (controlado pelo Playwright; usa o Chrome instalado no sistema).
- **Datas inválidas**: o script **não executa** em datas listadas em `data_invalidas.txt` (ex.: feriados nacionais e estaduais do RJ).
- **Log**: cada execução grava um arquivo em `logs/` com data e hora no nome (ex.: `rpa_web_20260303_142530.log`), registrando as ações e possíveis erros. Ao final da tarefa, o script **remove automaticamente** arquivos de log com mais de 10 dias.
- **Modo teste**: o argumento `--test` permite rodar a automação **sem executar o Passo 9** (clique no botão CONFIRMAR), útil para validar o fluxo até o botão "CONFIRMAR".

## Pré-requisitos

- **Sistema**: Windows (o script foi testado no Windows; Playwright também funciona em Linux/macOS).
- **Python**: 3.13+ (gerenciado pelo `uv`).
- **Ferramentas**:
  - [uv](https://docs.astral.sh/uv/)
  - Google Chrome instalado (o Playwright usa o Chrome do sistema por padrão).

## Configuração

### 1. Variáveis de ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto (se ainda não existir) com, por exemplo:

```env
USERNAME=seu_usuario_ou_email
PASSWORD=sua_senha
SITE=https://seu-site-alvo.com/

# IDs dos elementos do formulário (obrigatórios; inspecione a página com F12 para obter os valores)
ID_USERNAME=P101_USERNAME
ID_PASSWORD=P101_PASSWORD
ID_LOGIN=P101_LOGIN
ID_BOTAO_1=B491409282691032647
ID_BOTAO_2=B491409745545032651
```

- **`USERNAME` / `PASSWORD`**: credenciais de login.
- **`SITE`**: URL da página de login (com ou sem `https://`).
- **`ID_USERNAME`**: `id` do campo de usuário no HTML.
- **`ID_PASSWORD`**: `id` do campo de senha.
- **`ID_LOGIN`**: `id` do botão de login.
- **`ID_BOTAO_1`**: `id` do botão da primeira ação.
- **`ID_BOTAO_2`**: `id` do botão de confirmação final (Passo 9).

Todas as variáveis `ID_*` são **obrigatórias**. Se alguma não estiver definida, o script encerra com mensagem de erro indicando quais faltam.

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

### 3. Descobrir os IDs dos elementos

Os IDs são os atributos `id` dos elementos no HTML. Para obtê-los:

1. Abra o site no navegador e vá até a página de login (ou a tela com os botões de ação).
2. Pressione **F12** para abrir as Ferramentas do Desenvolvedor.
3. Use a ferramenta **Selecionar elemento** (ícone de seta) e clique no campo ou botão desejado.
4. No painel **Elements**, o elemento destacado terá algo como `id="P101_USERNAME"`. Use esse valor no `.env` (ex.: `ID_USERNAME=P101_USERNAME`).

Repita para o campo de senha, botão de login, botão 1 "Ação 1" e botão "CONFIRMAR" Ação 2, e preencha as variáveis correspondentes no `.env`.

## Como o script funciona

O `main.py` executa, em sequência:

1. **Verifica a data de hoje** em `data_invalidas.txt`. Se estiver na lista, exibe uma mensagem e encerra sem executar a automação.
2. Carrega o `.env` e valida se todas as variáveis `ID_*` estão definidas.
3. Abre o Chrome (via Playwright) na URL configurada e espera o formulário de login estar visível.
4. Preenche o campo de usuário e o campo de senha pelos IDs e clica no botão de login.
5. Aguarda a página pós-login carregar.
6. Clica no botão da primeira ação pelo ID.
7. Se não estiver em modo `--test`, clica no botão de confirmação final (Passo 9) pelo ID; se o botão estiver dentro de um modal com iframe, a automação tenta localizar o botão dentro do iframe e, em último caso, pelo texto **\"CONFIRMAR\"**.
8. Fecha o navegador.
9. **Remove arquivos de log** em `logs/` com mais de 10 dias (por data de modificação), para evitar acúmulo indefinido de arquivos.

A interação é feita pelo **Playwright**, que localiza os elementos pelo `id` no HTML, sem usar coordenadas da tela.

## Como rodar o projeto

Após clonar o repositório:

```bash
uv sync                    # instala as dependências (playwright, python-dotenv, etc.)
playwright install chrome  # instala o browser para o Playwright (ou use o Chrome já instalado)
uv run main.py             # executa a automação completa (todos os passos)
```

O script usa o Chrome instalado no sistema (`channel="chrome"`). Se preferir o Chromium gerenciado pelo Playwright, use `playwright install chromium` e ajuste o código para não usar `channel="chrome"`.

**Modo teste** (não executa o Passo 9 — clique no botão CONFIRMAR):

```bash
uv run main.py --test
```

Para ver a descrição do argumento:

```bash
uv run main.py --help
```

Se estiver em PowerShell e o uv mostrar o aviso de hardlink, veja a seção de troubleshooting abaixo.

## Modo de uso para teste

Use o argumento `--test` quando quiser:

- Validar o fluxo até o clique em "Ação 1" sem disparar o clique em **CONFIRMAR** (Passo 9).
- Evitar efeitos reais da ação do botão CONFIRMAR em ambiente de produção ou em testes rápidos.

O script registra no log que está em modo teste e que o Passo 9 foi ignorado. O restante da automação (login, botão Botão 1, fechamento do navegador) é executado normalmente.

| Comando | Passo 9 (botão CONFIRMAR) |
|--------|---------------------------|
| `uv run main.py` | Executado |
| `uv run main.py --test` | Não executado |

## Log de execuções

- **Pasta**: `logs/` (criada automaticamente na raiz do projeto).
- **Nome do arquivo**: `rpa_web_AAAAMMDD_HHMMSS.log` (data e hora do início da execução).
- **Conteúdo**: cada ação da automação (abertura do Chrome, preenchimento de campos, cliques, etc.) e, em caso de erro, o stack trace completo.
- **Retenção**: ao final de cada execução (sucesso ou falha), o script remove arquivos de log com **mais de 10 dias**, com base na data de modificação do arquivo. O período de retenção está definido em `main.py` na constante `DIAS_RETENCAO_LOG`.
- **Agendador de Tarefas**: o script encerra com código `0` em sucesso e `1` em falha; o histórico detalhado fica nos arquivos de log.

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
