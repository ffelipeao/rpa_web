import argparse
import os
import re
import subprocess
import time
from datetime import date, datetime
from pathlib import Path
import logging

import pyautogui
import pygetwindow as gw
import pyperclip
from dotenv import load_dotenv


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


def _parse_coords(value: str) -> tuple[int, int]:
    """Converte 'x=553, y=405' ou '553, 405' em (553, 405)."""
    if not value:
        raise ValueError("Coordenadas vazias")
    nums = re.findall(r"\d+", value)
    if len(nums) >= 2:
        return (int(nums[0]), int(nums[1]))
    raise ValueError(f"Coordenadas inválidas: {value!r}")

# Caminhos comuns do Chrome no Windows
CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

def _chrome_exe():
    for p in CHROME_PATHS:
        if p.exists():
            print(str(p))
            return str(p)
    return "chrome"  # fallback: usa o do PATH (se existir)


def _paste_text(text: str) -> None:
    """Cola texto via clipboard (evita problema com @, +, ?, etc. no pyautogui.write)."""
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")


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

        # pega só o primeiro "token" da linha (antes de espaços ou "-")
        token = line.split()[0]
        token = token.split("-", 1)[0].strip()
        if not token:
            continue

        for fmt in ("%d/%m/%Y", "%d/%m"):
            try:
                parsed = datetime.strptime(token, fmt).date()
                # se veio sem ano, trata como recorrente
                if fmt == "%d/%m":
                    if parsed.day == today.day and parsed.month == today.month:
                        return True
                else:
                    if parsed == today:
                        return True
                break
            except ValueError:
                continue

    return False

def main(*, test: bool = False) -> int:
    try:
        if test:
            logger.info("Modo teste ativo: Passo 9 (botão de ação 2) não será executado.")
        if _is_invalid_today():
            logger.info(
                "Data atual está na lista de datas inválidas (data_invalidas.txt). Automatização não será executada."
            )
            return 0

        logger.info("Iniciando o programa...")
        load_dotenv(override=True)  # override=True: .env sobrescreve USERNAME do Windows

        USERNAME = os.getenv("USERNAME", "")
        PASSWORD = os.getenv("PASSWORD", "")
        SITE = os.getenv("SITE", "").lower()
        EMAIL_FIELD = _parse_coords(os.getenv("EMAIL_FIELD", ""))
        BUTTON1 = _parse_coords(os.getenv("BUTTON1", ""))
        BUTTON2 = _parse_coords(os.getenv("BUTTON2", ""))

        logger.info("Configurações carregadas. SITE=%s, EMAIL_FIELD=%s, BUTTON1=%s, BUTTON2=%s",
                    SITE, EMAIL_FIELD, BUTTON1, BUTTON2)

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        # Passo 1: Entrar no site da empresa
        # Passo 2: Navegar até a página de login
        logger.info("Abrindo Chrome em modo anônimo na URL configurada.")
        url = SITE
        chrome = _chrome_exe()
        subprocess.Popen([chrome, "--incognito", url])
        time.sleep(7)  # esperar a janela anônima e a página carregar (aumente se a rede for lenta)

        # Maximizar o navegador (atalho Windows: Win+Up) só se ainda não estiver maximizado
        active = gw.getActiveWindow()
        if active is not None and not getattr(active, "isMaximized", False):
            logger.info("Maximizando janela ativa do navegador.")
            pyautogui.hotkey("win", "up")
            time.sleep(3)  # aguardar a animação de maximizar
        else:
            logger.info("Janela já está maximizada ou não foi possível obter janela ativa.")

        # Passo 3: Preencher o campo de e-mail
        logger.info("Preenchendo o campo de e-mail nas coordenadas %s.", EMAIL_FIELD)
        pyautogui.click(EMAIL_FIELD)
        time.sleep(3)  # dar foco ao campo antes de colar
        _paste_text(USERNAME)

        # Passo 4: Preencher o campo de senha
        logger.info("Preenchendo o campo de senha.")
        pyautogui.press("tab")
        time.sleep(3)  # Esperar para digitar a senha
        _paste_text(PASSWORD)

        # Passo 5: Clicar no botão de login
        logger.info("Clicando no botão de login (Enter).")
        time.sleep(3)
        pyautogui.press("enter")
        # Passo 6: Verificar se o login foi realizado com sucesso
        logger.info("Login: ação de envio executada. Verificando resultado visualmente na tela.")

        # Passo 7: Navegar até a página de ação 1
        # Passo 8: Clicar no botão de ação 1
        logger.info("Clicando no botão 1 nas coordenadas %s.", BUTTON1)
        time.sleep(0.5)
        pyautogui.click(BUTTON1)

        # Passo 9: Clicar no botão de ação 2 (omitido em modo --test)
        if not test:
            logger.info("Clicando no botão 2 nas coordenadas %s.", BUTTON2)
            time.sleep(0.5)
            pyautogui.click(BUTTON2)
        else:
            logger.info("Modo teste: Passo 9 (botão 2) ignorado.")

        # Passo 10: Clicar no botão de fechar janela
        logger.info("Fechando a janela do navegador (Alt+F4).")
        time.sleep(3)
        pyautogui.hotkey("alt", "f4")
        logger.info("Janela fechada com sucesso.")
        time.sleep(3)

        logger.info("Automatização concluída com sucesso.")
        return 0
    except Exception:
        logger.exception("Erro inesperado durante a execução da automatização.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatização RPA Web.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo teste: executa a automação sem o Passo 9 (clique no botão de ação 2).",
    )
    args = parser.parse_args()
    raise SystemExit(main(test=args.test))
