import logging
from fastapi import Request
from typing import Any
import contextvars, uuid
from src.config import settings

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")

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
audit_logger = logging.getLogger("audit")

def audit_log(*, action: str, actor_id: str | None, target: str | None, status: str, meta: dict[str, Any] | None = None) -> None:
    payload = {
        "action": action,
        "actor_id": actor_id,
        "target": target,
        "status": status,
        "meta": meta or {},
    }
    audit_logger.info("audit", extra={"request_id": get_request_id(), "audit": payload})
