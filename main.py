import argparse
import os
from datetime import date, datetime
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
ID_BOTAO_BATER_PONTO = os.getenv("ID_BOTAO_BATER_PONTO")
ID_BOTAO_CONFIRMAR = os.getenv("ID_BOTAO_CONFIRMAR")

# Timeouts em ms
TIMEOUT_NAVEGACAO = 30_000
TIMEOUT_ELEMENTO = 15_000
TIMEOUT_MODAL = 10_000


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
            "ID_BOTAO_BATER_PONTO": ID_BOTAO_BATER_PONTO,
            "ID_BOTAO_CONFIRMAR": ID_BOTAO_CONFIRMAR,
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
                logger.info("Preenchendo o campo de usuário (id=%s).", ID_USERNAME)
                page.locator(f"#{ID_USERNAME}").fill(USERNAME)

                # Passo 4: Preencher senha
                logger.info("Preenchendo o campo de senha (id=%s).", ID_PASSWORD)
                page.locator(f"#{ID_PASSWORD}").fill(PASSWORD)

                # Passo 5 e 6: Clicar no botão de login
                logger.info("Clicando no botão de login (id=%s).", ID_LOGIN)
                page.locator(f"#{ID_LOGIN}").click()
                page.wait_for_load_state("load", timeout=TIMEOUT_NAVEGACAO)
                # Aguarda a página pós-login (botão "Bater ponto" visível)
                page.locator(f"#{ID_BOTAO_BATER_PONTO}").wait_for(state="visible", timeout=TIMEOUT_ELEMENTO)
                logger.info("Login enviado. Página pós-login carregada.")

                # Passo 7 e 8: Clicar em "Bater ponto"
                logger.info("Clicando no botão Bater ponto (id=%s).", ID_BOTAO_BATER_PONTO)
                page.locator(f"#{ID_BOTAO_BATER_PONTO}").click()
                page.wait_for_timeout(1500)  # tempo para o modal abrir

                # Passo 9: Clicar em CONFIRMAR (omitido em modo --test)
                if not test:
                    logger.info("Clicando no botão CONFIRMAR (id=%s).", ID_BOTAO_CONFIRMAR)
                    try:
                        btn_confirmar = page.locator(f"#{ID_BOTAO_CONFIRMAR}")
                        btn_confirmar.wait_for(state="visible", timeout=TIMEOUT_MODAL)
                        btn_confirmar.click()
                    except PlaywrightTimeoutError:
                        # Pode estar dentro de um iframe/modal; tenta por texto
                        logger.info("Botão por ID não visível; tentando por texto 'CONFIRMAR'.")
                        page.get_by_role("button", name="CONFIRMAR").first.click()
                    page.wait_for_timeout(2000)
                else:
                    logger.info("Modo teste: Passo 9 (CONFIRMAR) ignorado.")

                logger.info("Automatização concluída com sucesso.")
            finally:
                page.wait_for_timeout(2_000)
                browser.close()

        return 0
    except PlaywrightTimeoutError as e:
        logger.exception("Timeout ao aguardar elemento ou navegação: %s", e)
        return 1
    except Exception:
        logger.exception("Erro inesperado durante a execução da automatização.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatização RPA Web (Playwright).")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo teste: executa a automação sem o Passo 9 (clique em CONFIRMAR).",
    )
    args = parser.parse_args()
    raise SystemExit(main(test=args.test))
