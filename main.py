import argparse
import os
from datetime import date, datetime, timedelta
from pathlib import Path
import logging

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Carrega .env antes de ler qualquer variável de ambiente usada no módulo
load_dotenv(override=True)

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"rpa_web_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# IDs dos elementos do formulário: vêm do .env (obrigatórios)
ID_USERNAME = os.getenv("ID_USERNAME")
ID_PASSWORD = os.getenv("ID_PASSWORD")
ID_LOGIN = os.getenv("ID_LOGIN")
ID_BOTAO_1 = os.getenv("ID_BOTAO_1")
ID_BOTAO_2 = os.getenv("ID_BOTAO_2")

# Timeouts em ms (tempo máximo de espera por navegação/elemento)
TIMEOUT_NAVEGACAO = 15_000
TIMEOUT_ELEMENTO = 15_000
TIMEOUT_MODAL = 15_000

# Pausa antes de cada ação na página (ms), para parecer mais humano e reduzir detecção de bot
PAUSA_ANTES_ACAO_MS = 3_000

# Quantidade de dias para manter arquivos de log; arquivos mais antigos são removidos ao final da tarefa
DIAS_RETENCAO_LOG = 10


def _remover_logs_antigos(dias: int = DIAS_RETENCAO_LOG) -> None:
    """Remove arquivos de log em LOG_DIR com mais de `dias` dias (por data de modificação)."""
    if not LOG_DIR.exists():
        return
    limite = (datetime.now() - timedelta(days=dias)).timestamp()
    removidos = 0
    for f in LOG_DIR.glob("*.log"):
        try:
            if f.stat().st_mtime < limite:
                f.unlink()
                removidos += 1
        except OSError:
            pass
    if removidos:
        logger.info("Removidos %d arquivo(s) de log com mais de %d dias.", removidos, dias)


def _is_invalid_today() -> bool:
    """Retorna True se a data de hoje estiver na lista de datas inválidas em data_invalidas.txt."""
    today = date.today()
    cfg_path = Path(__file__).resolve().parent / "data_invalidas.txt"
    if not cfg_path.exists():
        return False

    try:
        raw_text = cfg_path.read_text(encoding="utf-8")
    except OSError:
        return False

    for raw_line in raw_text.splitlines():
        # permite comentários com # e descrições após a data
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        token = line.split()[0]
        token = token.split("-", 1)[0].strip()
        if not token:
            continue

        for fmt in ("%d/%m/%Y", "%d/%m"):
            try:
                if fmt == "%d/%m":
                    # Ano explícito para evitar DeprecationWarning (Python 3.15+)
                    parsed = datetime.strptime(f"{token}/{today.year}", "%d/%m/%Y").date()
                    if parsed.day == today.day and parsed.month == today.month:
                        return True
                else:
                    parsed = datetime.strptime(token, fmt).date()
                    if parsed == today:
                        return True
                break
            except ValueError:
                continue

    return False


def main(*, test: bool = False) -> int:
    try:
        if test:
            logger.info("Modo teste ativo: Passo 9 (botão CONFIRMAR) não será executado.")
            
        # Não executa em fins de semana (sábado/domingo)
        if date.today().weekday() >= 5:
            logger.info("Hoje não é dia útil (sábado/domingo). Automatização não será executada.")
            return 0
        if _is_invalid_today():
            logger.info(
                "Data atual está na lista de datas inválidas (data_invalidas.txt). Automatização não será executada."
            )
            return 0

        logger.info("Iniciando o programa...")
        load_dotenv(override=True)

        # Valida variáveis de ambiente obrigatórias (IDs do formulário)
        ids_obrigatorios = {
            "ID_USERNAME": ID_USERNAME,
            "ID_PASSWORD": ID_PASSWORD,
            "ID_LOGIN": ID_LOGIN,
            "ID_BOTAO_1": ID_BOTAO_1,
            "ID_BOTAO_2": ID_BOTAO_2,
        }
        faltando = [k for k, v in ids_obrigatorios.items() if not (v and str(v).strip())]
        if faltando:
            logger.error(
                "Variáveis obrigatórias não configuradas no .env: %s. Defina todas antes de executar.",
                ", ".join(faltando),
            )
            return 1

        USERNAME = os.getenv("USERNAME", "")
        PASSWORD = os.getenv("PASSWORD", "")
        SITE = os.getenv("SITE", "").strip()
        if not SITE:
            logger.error("SITE não configurado no .env.")
            return 1
        if not SITE.startswith(("http://", "https://")):
            SITE = "https://" + SITE

        logger.info("Configurações carregadas. SITE=%s (login por IDs do formulário).", SITE)

        with sync_playwright() as p:
            # Usa o Chrome instalado; modo anônimo via context
            browser = p.chromium.launch(
                channel="chrome",
                headless=False,
            )
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(TIMEOUT_ELEMENTO)
            page.set_default_navigation_timeout(TIMEOUT_NAVEGACAO)

            try:
                # Passo 1 e 2: Abrir site e carregar página de login
                logger.info("Abrindo %s", SITE)
                page.goto(SITE, wait_until="domcontentloaded")
                page.wait_for_load_state("load", timeout=TIMEOUT_NAVEGACAO)
                # Aguarda o formulário de login estar visível (mais confiável que networkidle)
                page.locator(f"#{ID_USERNAME}").wait_for(state="visible", timeout=TIMEOUT_ELEMENTO)

                # Passo 3: Preencher usuário
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                logger.info("Preenchendo o campo de usuário (id=%s).", ID_USERNAME)
                page.locator(f"#{ID_USERNAME}").fill(USERNAME)

                # Passo 4: Preencher senha
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                logger.info("Preenchendo o campo de senha (id=%s).", ID_PASSWORD)
                page.locator(f"#{ID_PASSWORD}").fill(PASSWORD)

                # Passo 5 e 6: Clicar no botão de login
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                logger.info("Clicando no botão de login (id=%s).", ID_LOGIN)
                page.locator(f"#{ID_LOGIN}").click()
                page.wait_for_load_state("load", timeout=TIMEOUT_NAVEGACAO)
                page.locator(f"#{ID_BOTAO_1}").wait_for(state="visible", timeout=TIMEOUT_ELEMENTO)
                logger.info("Login enviado. Página pós-login carregada.")

                # Passo 7 e 8: Botão de ação 1
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                logger.info("Clicando no botão de ação 1 (id=%s).", ID_BOTAO_1)
                page.locator(f"#{ID_BOTAO_1}").click()
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)

                # Passo 9: Clicar em CONFIRMAR dentro do modal (botão está no iframe do modal)
                if not test:
                    page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                    logger.info("Aguardando modal e clicando no botão de ação 2 (id=%s) dentro do iframe.", ID_BOTAO_2)
                    try:
                        # Aguarda o modal estar visível
                        page.locator(".vch-modal-dialog.modal").wait_for(state="visible", timeout=TIMEOUT_MODAL)
                        # O botão CONFIRMAR está dentro do iframe do modal
                        frame = page.frame_locator(".vch-modal-iframe")
                        btn_confirmar = frame.locator(f"#{ID_BOTAO_2}")
                        btn_confirmar.wait_for(state="visible", timeout=TIMEOUT_MODAL)
                        logger.info("Opção 1: Clicando no botão de ação 2 (id=%s) dentro do iframe.", ID_BOTAO_2)
                        btn_confirmar.click()
                    except PlaywrightTimeoutError:
                        # Fallback: botão por texto dentro do iframe
                        frame = page.frame_locator(".vch-modal-iframe")
                        logger.info("Opção 2: Clicando no botão de ação 2 (texto=CONFIRMAR) dentro do iframe.")
                        frame.get_by_role("button", name="CONFIRMAR").first.click()
                    page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                else:
                    logger.info("Modo teste: Passo 9 (CONFIRMAR) ignorado.")

                logger.info("Automatização concluída com sucesso.")
            finally:
                page.wait_for_timeout(PAUSA_ANTES_ACAO_MS)
                browser.close()

        return 0
    except PlaywrightTimeoutError as e:
        logger.exception("Timeout ao aguardar elemento ou navegação: %s", e)
        return 1
    except Exception:
        logger.exception("Erro inesperado durante a execução da automatização.")
        return 1
    finally:
        _remover_logs_antigos()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatização web (Playwright).")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo teste: executa a automação sem o Passo 9 (clique em CONFIRMAR).",
    )
    args = parser.parse_args()
    raise SystemExit(main(test=args.test))
