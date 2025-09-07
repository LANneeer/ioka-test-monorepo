import logging
from fastapi import Request
from typing import Any
import contextvars, uuid
from src.config import settings
from logstash_async.handler import AsynchronousLogstashHandler
from logstash_async.formatter import LogstashFormatter

logstash_handler = AsynchronousLogstashHandler(
    host=settings.LOGSTASH_HOST,
    port=settings.LOGSTASH_PORT,
    database_path=None
)
logstash_handler.setFormatter(LogstashFormatter())

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    handlers=[logging.StreamHandler(), logstash_handler],
)
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
audit_logger = logging.getLogger("audit")

def extract_request_id(request: Request) -> str:
    rid = request.headers.get(settings.REQUEST_ID_HEADER) or str(uuid.uuid4())
    request_id_ctx.set(rid)
    return rid

def get_request_id() -> str:
    rid = request_id_ctx.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_ctx.set(rid)
    return rid

def audit_log(*, action: str, actor_id: str | None, target: str | None, status: str, meta: dict[str, Any] | None = None) -> None:
    payload = {
        "action": action,
        "actor_id": actor_id,
        "target": target,
        "status": status,
        "meta": meta or {},
    }
    audit_logger.info("audit", extra={"request_id": get_request_id(), "audit": payload})
