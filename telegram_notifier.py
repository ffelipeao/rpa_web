"""Envio de alertas ao Telegram após cada execução do RPA (usa apenas a biblioteca padrão)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Final
from zoneinfo import ZoneInfo

# Resultado lógico da execução (usado para montar a mensagem)
OUTCOME_SKIPPED_WEEKEND: Final = "skipped_weekend"
OUTCOME_SKIPPED_INVALID_DATE: Final = "skipped_invalid_date"
OUTCOME_CONFIG_ERROR: Final = "config_error"
OUTCOME_SUCCESS_TEST: Final = "success_test"
OUTCOME_SUCCESS_FULL: Final = "success_full"
OUTCOME_ERROR: Final = "error"


@dataclass(frozen=True)
class RunReport:
    """Resumo de uma execução de `main()` para o alerta."""

    executed_at: datetime
    test_mode: bool
    outcome: str
    exit_code: int

    @property
    def automation_finished_ok(self) -> bool:
        """Fluxo Playwright chegou ao fim sem erro (modo normal ou teste)."""
        return self.outcome in (OUTCOME_SUCCESS_FULL, OUTCOME_SUCCESS_TEST) and self.exit_code == 0

    @property
    def confirmation_step_executed(self) -> bool:
        """Passo 9 (CONFIRMAR) foi de fato executado (não é modo teste)."""
        return self.outcome == OUTCOME_SUCCESS_FULL and self.exit_code == 0


class TelegramGroupAlert:
    """
    Envia uma mensagem a um grupo (ou chat) do Telegram usando a Bot API.

    Variáveis de ambiente (opcionais): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
    Se faltar alguma, o envio é ignorado e um aviso é registrado no log.
    """

    _API_BASE: Final = "https://api.telegram.org"

    def __init__(
        self,
        *,
        bot_token: str | None = None,
        chat_id: str | None = None,
        timezone: str = "America/Sao_Paulo",
        logger: logging.Logger | None = None,
    ) -> None:
        self._token = (bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
        self._chat_id = (chat_id if chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "")).strip()
        self._tz = ZoneInfo(timezone)
        self._log = logger or logging.getLogger(__name__)

    def is_enabled(self) -> bool:
        if os.getenv("TELEGRAM_ALERTS", "1").strip().lower() in ("0", "false", "no", "off"):
            return False
        return bool(self._token and self._chat_id)

    def notify_run(self, report: RunReport) -> None:
        """Envia o resumo da execução. Falhas de rede não interrompem o processo."""
        if not self.is_enabled():
            if self._token or self._chat_id:
                self._log.debug("Alerta Telegram desativado ou token/chat incompleto; envio ignorado.")
            return
        text = self._format_message(report)
        try:
            self._send_message(text)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            self._log.warning("Telegram HTTP %s: %s", e.code, body[:500])
        except urllib.error.URLError as e:
            self._log.warning("Telegram rede/URL: %s", e.reason)
        except OSError as e:
            self._log.warning("Telegram I/O: %s", e)

    def _format_message(self, r: RunReport) -> str:
        local = r.executed_at.astimezone(self._tz)
        data_hora = local.strftime("%Y-%m-%d %H:%M:%S %Z")
        modo_teste = "Sim" if r.test_mode else "Não"

        if r.outcome == OUTCOME_SKIPPED_WEEKEND:
            situacao = "Não iniciada — fim de semana (sábado/domingo)."
        elif r.outcome == OUTCOME_SKIPPED_INVALID_DATE:
            situacao = "Não iniciada — data na lista de datas inválidas."
        elif r.outcome == OUTCOME_CONFIG_ERROR:
            situacao = "Encerrada com erro de configuração (.env / SITE / IDs)."
        elif r.outcome == OUTCOME_SUCCESS_TEST:
            situacao = "Fluxo concluído em modo teste (Passo 9 / CONFIRMAR não executado)."
        elif r.outcome == OUTCOME_SUCCESS_FULL:
            situacao = "Fluxo concluído; Passo 9 (CONFIRMAR) executado."
        elif r.outcome == OUTCOME_ERROR:
            situacao = "Encerrada com erro (timeout ou exceção durante a automação)."
        else:
            situacao = f"Estado desconhecido: {r.outcome!r}."

        fluxo_ok = "Sim" if r.automation_finished_ok else "Não"
        confirmou = "Sim" if r.confirmation_step_executed else "Não"
        codigo = f"{r.exit_code}"

        # "Operação realmente finalizada" = confirmação real no alvo (não modo teste)
        operacao_ponta_a_ponta = "Sim" if r.confirmation_step_executed else "Não"

        return (
            "<b>RPA Web — fim de execução</b>\n"
            f"Data/hora: <code>{data_hora}</code>\n"
            f"Modo teste: <b>{modo_teste}</b>\n"
            f"Código de saída: <code>{codigo}</code>\n"
            f"Situação: {situacao}\n"
            f"Automação concluída com sucesso: <b>{fluxo_ok}</b>\n"
            f"Passo 9 (CONFIRMAR) executado: <b>{confirmou}</b>\n"
            f"Operação finalizada de ponta a ponta (confirmação real): <b>{operacao_ponta_a_ponta}</b>"
        )

    def _send_message(self, text: str) -> None:
        url = f"{self._API_BASE}/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                self._log.warning("Telegram resposta HTTP %s", resp.status)
            else:
                self._log.info("Telegram: mensagem enviada com sucesso.")
