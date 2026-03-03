# Passo 1: Entrar no site da empresa
# Passo 2: Navegar até a página de login
# Passo 3: Preencher o campo de e-mail
# Passo 4: Preencher o campo de senha
# Passo 5: Clicar no botão de login
# Passo 6: Verificar se o login foi realizado com sucesso
# Passo 7: Navegar até a página de ação 1
# Passo 8: Clicar no botão de ação 1
# Passo 9: Clicar no botão de ação 2
# Passo 10: Clicar no botão de fechar janela

import os
import re
import subprocess
import time
from pathlib import Path

import pyautogui
import pyperclip
from dotenv import load_dotenv


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

def login():
    print("Iniciando o programa...")
    load_dotenv(override=True)  # override=True: .env sobrescreve USERNAME do Windows

    USERNAME = os.getenv("USERNAME", "")
    PASSWORD = os.getenv("PASSWORD", "")
    SITE = os.getenv("SITE", "").lower()
    EMAIL_FIELD = _parse_coords(os.getenv("EMAIL_FIELD", ""))
    PASSWORD_FIELD = _parse_coords(os.getenv("PASSWORD_FIELD", ""))
    LOGIN_BUTTON = _parse_coords(os.getenv("LOGIN_BUTTON", ""))
    BUTTON1 = _parse_coords(os.getenv("BUTTON1", ""))
    BUTTON2 = _parse_coords(os.getenv("BUTTON2", ""))
    FECHAR_WINDOW = _parse_coords(os.getenv("FECHAR_WINDOW", ""))
    
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
    pyautogui.alert("O programa está sendo executado. Não mexa no mouse ou teclado.")

    url = SITE
    chrome = _chrome_exe()
    subprocess.Popen([chrome, "--incognito", url])
    time.sleep(5)  # esperar a janela anônima e a página carregar (aumente se a rede for lenta)

    print("Preenchendo o campo de e-mail...")
    pyautogui.click(EMAIL_FIELD)
    time.sleep(0.4)  # dar foco ao campo antes de colar
    _paste_text(USERNAME)

    print("Preenchendo o campo de senha...")
    pyautogui.click(PASSWORD_FIELD)
    time.sleep(0.4) # dar foco ao campo antes de colar
    _paste_text(PASSWORD)

    print("Clicando no botão de login...")
    time.sleep(0.3)
    pyautogui.click(LOGIN_BUTTON)
    print("Login realizado com sucesso!")

    print("Clicando no botão 1.")
    time.sleep(0.5)
    pyautogui.click(BUTTON1)

    print("Clicando no botão 2.")
    time.sleep(0.5)
    pyautogui.click(BUTTON2)

    print("Clicando no botão de fechar janela...")
    time.sleep(0.5)
    pyautogui.click(FECHAR_WINDOW)
    print("Janela fechada com sucesso!")

if __name__ == "__main__":
    login()
