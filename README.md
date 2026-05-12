# rpa_web

Automação RPA (Robotic Process Automation) que faz login em um sistema web e executa tarefas usando **Playwright**, interagindo com os elementos da página pelos **IDs do formulário** (sem depender de coordenadas da tela).

## Visão geral

- **Objetivo**: abrir o site alvo, fazer login (usuário e senha) e executar sequências de cliques (ex.: botões pós-login).
- **Automação**: baseada nos **IDs dos elementos** (campos e botões) definidos no arquivo `.env`. O Playwright localiza os elementos pelo `id` no HTML, evitando erros quando a tela ou a resolução mudam.
- **Navegador**: por padrão o **Chromium** instalado pelo Playwright (`uv run playwright install chromium`), em modo **sem janela (headless)** — adequado a terminal, `cron` e servidores. Use `HEADLESS=0` no `.env` para ver a janela. Se quiser usar o **Google Chrome** já instalado no sistema, defina `PLAYWRIGHT_CHANNEL=chrome` no `.env` (em servidor sem Chrome, não use essa variável).
- **Dias de execução**: a automação só roda em **dias úteis (segunda a sexta)**. Sábados e domingos são ignorados automaticamente.
- **Datas inválidas**: o script **não executa** em datas listadas em `data_invalidas.txt` (ex.: feriados nacionais e estaduais do RJ).
- **Log**: um arquivo por dia em `logs/` (`run_YYYYMMDD.log`, modo **append**), com bloco separado por execução; registra ações e possíveis erros. Ao final da tarefa, o script **remove automaticamente** arquivos de log com mais de 10 dias.
- **Telegram**: ao **final de toda execução** (incluindo quando o fluxo não inicia por fim de semana, data em `data_invalidas.txt` ou erro de configuração), pode enviar um **resumo em HTML** para um grupo ou chat, via [Bot API](https://core.telegram.org/bots/api), se `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` estiverem definidos no `.env`. O envio usa só a biblioteca padrão (`urllib`); falhas de rede **não** interrompem o script (apenas aviso no log). Desative com `TELEGRAM_ALERTS=0` se quiser manter o restante igual sem notificações.
- **Modo teste**: o argumento `--test` permite rodar a automação **sem executar o Passo 9** (clique no botão CONFIRMAR), útil para validar o fluxo até o botão "CONFIRMAR".

## Pré-requisitos

- **Sistema**: Windows (o script foi testado no Windows; Playwright também funciona em Linux/macOS).
- **Python**: 3.14+ (gerenciado pelo `uv`).
- **Ferramentas**:
  - [uv](https://docs.astral.sh/uv/)
  - **Chromium do Playwright** (instalado com `uv run playwright install chromium` após o `uv sync`; ver seção Configuração). **Google Chrome** no sistema só é necessário se você definir `PLAYWRIGHT_CHANNEL=chrome` no `.env`.

### Instalar o `uv` (macOS)

Se você ainda não tiver o `uv` instalado:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

## Configuração

### 0. Dependências Python e Chromium do Playwright

Na raiz do projeto (após clonar), instale o ambiente e o binário do navegador usado pelo script. A ordem importa: primeiro o `uv sync`, depois o `playwright install`.

```bash
uv sync
uv run playwright install chromium
```

- O pacote **playwright** no PyPI traz só a biblioteca Python; o **Chromium** vem do segundo comando. Faça isso **uma vez** por máquina ou sempre que recriar o `.venv` de propósito.
- Em Linux minimalista, se faltar biblioteca do sistema: `uv run playwright install-deps chromium` (às vezes com `sudo`).
- Atalho equivalente aos dois primeiros comandos: `./scripts/bootstrap.sh` (deixe executável com `chmod +x scripts/bootstrap.sh` se necessário).

### 1. Variáveis de ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto (se ainda não existir) com, por exemplo:

```env
USERNAME=seu_usuario_ou_email
PASSWORD=sua_senha
SITE=https://seu-site-alvo.com/

# Opcional: 1 (padrão) = sem janela. 0 = janela visível para depuração.
# HEADLESS=1

# IDs dos elementos do formulário (obrigatórios; inspecione a página com F12 para obter os valores)
ID_USERNAME=ID_USERNAME
ID_PASSWORD=ID_PASSWORD
ID_LOGIN=ID_LOGIN
ID_BOTAO_1=ID_BOTAO_1
ID_BOTAO_2=ID_BOTAO_2

# Opcional: alertas ao fim de cada execução (ver seção "Telegram" abaixo)
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
# TELEGRAM_CHAT_ID=-1001234567890
# TELEGRAM_ALERTS=0   # desliga todos os envios mantendo o script igual
```

> **HEADLESS — em destaque**  
> Variável **opcional**. Se você **não** definir, o script assume **`1`**: navegador **sem janela** (terminal, `cron`, servidor). Defina **`HEADLESS=0`** no `.env` quando quiser **ver o navegador** ao depurar. O arquivo **`.env.example`** na raiz repete esse bloco comentado para copiar ao criar o seu `.env`.

- **`USERNAME` / `PASSWORD`**: credenciais de login.
- **`HEADLESS`**: opcional; `1` ou omitido = sem janela; `0` = janela visível (depuração). Mesma regra descrita no destaque acima e em `.env.example`.
- **`SITE`**: URL da página de login (com ou sem `https://`).
- **`ID_USERNAME`**: `id` do campo de usuário no HTML.
- **`ID_PASSWORD`**: `id` do campo de senha.
- **`ID_LOGIN`**: `id` do botão de login.
- **`ID_BOTAO_1`**: `id` do botão da primeira ação.
- **`ID_BOTAO_2`**: `id` do botão de confirmação final (Passo 9).

Todas as variáveis `ID_*` são **obrigatórias**. Se alguma não estiver definida, o script encerra com mensagem de erro indicando quais faltam.

> **Importante**: o arquivo `.env` contém senha e pode conter o token do bot. Não envie esse arquivo para o Git / repositórios remotos.

### 1b. Telegram (alertas opcionais)

O módulo `telegram_notifier.py` envia **uma mensagem por execução** no bloco `finally` de `main.py`: ao sair de `main()`, o fluxo chama `_remover_logs_antigos()` e, em seguida, `TelegramGroupAlert.notify_run()` — inclusive quando a execução encerra cedo (fim de semana, data inválida ou erro de configuração).

| Variável | Obrigatória | Descrição |
| -------- | ----------- | --------- |
| `TELEGRAM_BOT_TOKEN` | Não | Token do bot criado com [@BotFather](https://t.me/BotFather). |
| `TELEGRAM_CHAT_ID` | Não | ID do grupo, canal ou chat (ex.: `-1001234567890` para supergrupos/canais). |
| `TELEGRAM_ALERTS` | Não | Padrão `1`. Valores como `0`, `false`, `no`, `off` desativam o envio (útil em máquinas de desenvolvimento). |

É necessário preencher **os dois** (`token` e `chat_id`) para haver envio; se qualquer um estiver vazio, o envio é ignorado. Com `TELEGRAM_ALERTS=0`, o envio também não ocorre (mensagem em nível `DEBUG` no log se token ou chat estiver parcialmente configurado).

**Conteúdo típico da mensagem**: título "RPA Web — fim de execução", data/hora (fuso `America/Sao_Paulo`), se rodou em modo teste (`--test`), código de saída, texto da situação (ex.: não iniciada por fim de semana, data inválida, erro de configuração, sucesso com ou sem Passo 9, ou erro na automação), se o fluxo Playwright terminou com sucesso, se o Passo 9 (CONFIRMAR) foi executado e se houve "operação de ponta a ponta" (confirmação real, não modo teste).

**Como obter o `chat_id`**: adicione o bot ao grupo, envie uma mensagem e consulte `getUpdates` na API, ou use um bot auxiliar (ex.: @userinfobot) conforme a documentação do Telegram — o `.env.example` traz comentários resumidos.

Erros HTTP ou de rede ao Telegram são registrados com `WARNING` no log; o processo já encerrou com o código de saída normal do RPA.

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

1. **Verifica se hoje é dia útil** (segunda a sexta). Se for sábado ou domingo, exibe uma mensagem e encerra sem executar a automação.
2. **Verifica a data de hoje** em `data_invalidas.txt`. Se estiver na lista, exibe uma mensagem e encerra sem executar a automação.
3. Carrega o `.env` e valida se todas as variáveis `ID_`* estão definidas.
4. Abre o Chromium do Playwright ou o Chrome do sistema (se `PLAYWRIGHT_CHANNEL=chrome` no `.env`), em headless por padrão, na URL configurada e espera o formulário de login estar visível.
5. Preenche o campo de usuário e o campo de senha pelos IDs e clica no botão de login.
6. Aguarda a página pós-login carregar.
7. Clica no botão da primeira ação pelo ID.
8. Se não estiver em modo `--test`, clica no botão de confirmação final (Passo 9) pelo ID; se o botão estiver dentro de um modal com iframe, a automação tenta localizar o botão dentro do iframe e, em último caso, pelo texto **CONFIRMAR**.
9. Fecha o navegador.
10. **Remove arquivos de log** em `logs/` com mais de 10 dias (por data de modificação), para evitar acúmulo indefinido de arquivos.
11. **Notificação Telegram** (se habilitada): após a remoção de logs antigos, no `finally`, chama `TelegramGroupAlert.notify_run()` com o `RunReport` da execução — inclusive quando os passos iniciais encerram cedo (fim de semana ou data inválida) ou há erro de configuração.

A interação é feita pelo **Playwright**, que localiza os elementos pelo `id` no HTML, sem usar coordenadas da tela.

## Como rodar o projeto

Ordem recomendada (alinhada à seção **Configuração**):

```bash
uv sync
uv run playwright install chromium
# Crie e preencha o .env (variáveis SITE, USERNAME, PASSWORD, ID_*)
uv run main.py --test      # recomendado: valida o fluxo sem o Passo 9 (CONFIRMAR)
uv run main.py             # automação completa
```

Sem o `playwright install chromium`, o primeiro `uv run main.py` tende a falhar por falta do binário do navegador. Chrome do sistema só entra no fluxo se você definir `PLAYWRIGHT_CHANNEL=chrome` no `.env`.

## Agendamento de Tarefas

Como o `main.py` já verifica **dias úteis (segunda a sexta)** e consulta `data_invalidas.txt`, você pode agendar com frequência maior (ex.: 1x por dia) e ele simplesmente encerra quando não for permitido.

### macOS e Linux (crontab)

- Garanta que você consegue rodar manualmente: `uv sync`, `uv run playwright install chromium` e `uv run main.py`.
- Edite a crontab: `crontab -e`.
- Adicione uma linha (exemplo: todo dia 09:00):

```cron
0 9 * * * /bin/bash -lc 'cd /Users/SEU_USUARIO/GitHub/rpa_web && ~/.local/bin/uv run main.py'
```

Observações:
- No `cron`, o PATH é mais “limpo”; por isso use caminho absoluto para o `uv` e para o diretório do projeto.
- Com headless ativo (padrão), não é necessário sessão gráfica no servidor; o navegador é o Chromium do Playwright, salvo se você usar `PLAYWRIGHT_CHANNEL=chrome`.

Se preferir rodar só em dias úteis (segunda a sexta), use:

```cron
0 9 * * 1-5 /bin/bash -lc 'cd /Users/SEU_USUARIO/GitHub/rpa_web && ~/.local/bin/uv run main.py'
```

### Windows (Agendador de Tarefas)

- Verifique antes manualmente: `uv sync`, `uv run playwright install chromium` e `uv run main.py`.
- Abra o **Agendador de Tarefas**.
- Crie uma tarefa (exemplo: nome `rpa_web` e gatilho diário às 09:00, ou a frequência que você preferir).
- Em **Ação**, selecione “Iniciar um programa”.
- Para evitar problema de PATH, use `cmd.exe`:

- **Programa/script**: `cmd.exe`
- **Argumentos** (ajuste o caminho):

```text
/c "cd /d C:\CAMINHO\PARA\rpa_web && uv run main.py"
```

Observações:
- Se o `uv` não for encontrado pelo Agendador, descubra o caminho com `where uv` e use o caminho completo do `uv.exe`.
- Com headless ativo (padrão), a tarefa pode rodar mesmo sem usuário conectado à área de trabalho (ajuste permissões de rede e PATH conforme seu ambiente).

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


| Comando                 | Passo 9 (botão CONFIRMAR) |
| ----------------------- | ------------------------- |
| `uv run main.py`        | Executado                 |
| `uv run main.py --test` | Não executado             |


## Log de execuções

- **Pasta**: `logs/` (criada automaticamente na raiz do projeto).
- **Nome do arquivo**: `run_YYYYMMDD.log` (**um arquivo por dia**, novas execuções do mesmo dia são **anexadas**; cada execução começa com um cabeçalho de sessão e as linhas seguintes ficam indentadas no arquivo).
- **Conteúdo**: cada etapa relevante (abertura do site, preenchimento de campos, cliques, etc.) e, em caso de erro, o stack trace completo.
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