# Agendamento com cron (macOS / Linux)

Este guia explica como incluir as execuções automáticas do projeto no **crontab**, com uma pequena **aleatoriedade** no horário (até ~5 minutos após o minuto base), para simular variação natural de entrada, almoço, retorno e saída.

## Ajustar caminhos antes de colar

Nos exemplos abaixo, `**USERNAME`** é um **marcador**: troque pelo **nome curto do seu usuário** no Linux (em geral o retorno de `whoami` ou o nome da pasta em `/home/…`).

Os caminhos seguem o **padrão Linux** (`/home/USERNAME/…`). No **macOS**, o diretório pessoal costuma ser `/Users/USERNAME/…` — ajuste todos os prefixos se for usar o mesmo trecho no macOS.

**Todos os caminhos absolutos** precisam ser **revisados e ajustados** conforme a sua máquina: pasta onde o repositório foi clonado, local real do executável `uv` (`which uv`) e, se usar log em arquivo, o destino do redirecionamento.

## Pré-requisitos

- **Caminho do projeto**: use o diretório real do clone (ex.: `/home/USERNAME/GitHub/rpa_web` ou outro caminho à sua escolha).
- `**uv`**: o exemplo usa `/home/USERNAME/.local/bin/uv`. Confirme com `which uv` e substitua se for outro caminho.
- **Shell**: as linhas usam `/bin/zsh`. Se não tiver `zsh`, troque por `/bin/bash` (comum em instalações Linux mínimas).

## O que cada linha faz


| Agendamento | Janela aproximada (dias úteis) |
| ----------- | ------------------------------ |
| Entrada     | entre **07:55** e **08:05**    |
| Almoço      | entre **11:59** e **12:09**    |
| Retorno     | entre **13:00** e **13:10**    |
| Saída       | entre **17:15** e **17:25**    |


O `sleep $(( RANDOM \% 300 ))` atrasa de **0 a 299 segundos** (~0 a ~5 minutos) após o minuto em que o cron dispara o job.

**Nota:** no arquivo `crontab`, o caractere `**%` é especial** (em muitos sistemas vira quebra de linha / restante vira stdin). Por isso use `**RANDOM \% 300`** dentro do `crontab -e`. Se você testar o mesmo `sleep` direto no terminal interativo, aí sim use `%` sem barra.

## Como incluir no crontab

1. Abra o editor do crontab do seu usuário:
  ```bash
   crontab -e
  ```
2. Cole as linhas abaixo, **substituindo `USERNAME` e conferindo cada caminho**, e salve.
3. Liste para conferir:
  ```bash
   crontab -l
  ```

### Linhas sugeridas

```cron
# rpa_web — dias úteis (segunda a sexta); aleatoriedade até ~5 min após o minuto base

# Entrada (entre 7:55 e 8:00)
55 7 * * 1-5 /bin/zsh -c 'sleep $(( RANDOM \% 300 )); cd /home/USERNAME/GitHub/rpa_web && /home/USERNAME/.local/bin/uv run main.py'

# Almoço (entre 11:59 e 12:04)
59 11 * * 1-5 /bin/zsh -c 'sleep $(( RANDOM \% 300 )); cd /home/USERNAME/GitHub/rpa_web && /home/USERNAME/.local/bin/uv run main.py'

# Retorno (entre 13:00 e 13:05)
0 13 * * 1-5 /bin/zsh -c 'sleep $(( RANDOM \% 300 )); cd /home/USERNAME/GitHub/rpa_web && /home/USERNAME/.local/bin/uv run main.py'

# Saída (entre 17:15 e 17:20)
15 17 * * 1-5 /bin/zsh -c 'sleep $(( RANDOM \% 300 )); cd /home/USERNAME/GitHub/rpa_web && /home/USERNAME/.local/bin/uv run main.py'
```

## Formato do cron (referência rápida)

```
minuto hora dia_mês mês dia_semana comando
```

- `55 7 * * 1-5` → às **07:55**, todo dia do mês, todo mês, **segunda a sexta**.
- `1-5` = segunda (1) até sexta (5) no cron do macOS/Linux.

## Ambiente e variáveis

O cron roda com um ambiente **mínimo** (poucas variáveis de ambiente, sem o mesmo `PATH` do terminal interativo). Por isso o exemplo usa **caminhos absolutos** para `zsh`, pasta do projeto e `uv`.

Se o script depender de variáveis do `.env`, garanta que `main.py` as carregue (por exemplo via arquivo `.env` no diretório do projeto) ou exporte o que for necessário no próprio comando.

## Logs (opcional)

Para depurar falhas silenciosas, você pode redirecionar saída para um arquivo:

```cron
55 7 * * 1-5 /bin/zsh -c 'sleep $(( RANDOM \% 300 )); cd /home/USERNAME/GitHub/rpa_web && /home/USERNAME/.local/bin/uv run main.py >> /home/USERNAME/GitHub/rpa_web/logs/cron.log 2>&1'
```

Crie a pasta `logs` antes, se usar esse padrão.

## macOS: permissões

Em versões recentes do macOS, o **Terminal** (ou o app que executa o cron) pode precisar de permissões em **Ajustes do Sistema → Privacidade e Segurança** (por exemplo Acessibilidade, Automação, Disco completo), dependendo do que o `main.py` fizer na máquina.

## Remover as entradas

```bash
crontab -e
```

Apague as linhas correspondentes e salve.