import asyncio
import json
import zlib
import time
from dataclasses import dataclass
from typing import Optional
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
from src.config import settings
from src.infrastructure.logging import get_request_id, logging

logger = logging.getLogger("cached")
REQS = Counter("http_requests_total", "Total HTTP requests", ["method","path","status"])
LAT  = Histogram("http_request_duration_seconds", "Latency", ["method","path","status"])


@dataclass
class CachedResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def to_bytes(self) -> bytes:
        payload = json.dumps({
            "status": self.status,
            "headers": self.headers,
            "body": self.body.decode("utf-8", "ignore"),
        }).encode("utf-8")
        return zlib.compress(payload)

    @staticmethod
    def from_bytes(b: bytes) -> "CachedResponse":
        data = json.loads(zlib.decompress(b).decode("utf-8"))
        return CachedResponse(
            status=data["status"],
            headers=data["headers"],
            body=data["body"].encode("utf-8"),
        )

def make_key(request: Request) -> str:
    idem_hdr = request.headers.get("Idempotency-Key", "")
    return f"idem:{request.method}:{request.url.path}:{idem_hdr}"

class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis: Optional[Redis] = None
        self._init_lock = asyncio.Lock()

    async def _ensure(self):
        if self.redis is None:
            async with self._init_lock:
                if self.redis is None:
                    self.redis = await Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)

    async def dispatch(self, request: Request, call_next):
        await self._ensure()
        key = make_key(request)

        if request.method in ("GET", "HEAD", "DELETE"):
            cached = await self.redis.get(key)
            if cached:
                cr = CachedResponse.from_bytes(cached)
                logger.info("Idempotency hit", extra={"request_id": get_request_id(), "audit": {"idempotency": "hit","key": key}})
                return Response(content=cr.body, status_code=cr.status, headers=cr.headers)

            response: Response = await call_next(request)
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            new_resp = Response(content=body, status_code=response.status_code, headers=dict(response.headers))

            cr = CachedResponse(status=new_resp.status_code, headers=dict(new_resp.headers), body=body)
            await self.redis.setex(key, settings.IDEMPOTENCY_TTL_SEC, cr.to_bytes())
            logger.info("Idempotency store", extra={"request_id": get_request_id(), "audit": {"idempotency": "store","key": key}})
            return new_resp

        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        dur = time.perf_counter() - start
        REQS.labels(request.method, request.url.path, response.status_code).inc()
        LAT.labels(request.method, request.url.path, response.status_code).observe(dur)
        return response

def prom_endpoint():
    data = generate_latest()
    return data, CONTENT_TYPE_LATEST
