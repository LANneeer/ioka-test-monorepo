import logging
import aiohttp
from src.config import settings
from src.infrastructure.logging import audit_log

log = logging.getLogger("notifier")

class Notifier:
    async def send_telegram(self, text: str) -> None:
        if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID):
            # мок: просто лог
            log.info("telegram_mock", extra={"audit": {"type": "notify", "channel": "telegram", "text": text}})
            return
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as sess:
            async with sess.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}) as resp:
                if resp.status != 200:
                    log.error("telegram_failed", extra={"audit": {"type": "notify_fail","status": resp.status}})
                else:
                    log.info("telegram_ok", extra={"audit": {"type": "notify_ok"}})

    async def transaction_status(self, *, tx_id: str, status: str, amount: str, from_acc: str, to_acc: str) -> None:
        txt = f"TX {tx_id}: {status} {amount} {from_acc}->{to_acc}"
        await self.send_telegram(txt)
        audit_log(action="tx.notify", actor_id=None, target=tx_id, status="success", meta={"status": status})
