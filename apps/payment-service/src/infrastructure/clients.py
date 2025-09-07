from uuid import UUID
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional, Dict, Any
from decimal import Decimal
import asyncio
import aiohttp
import json
import time

import redis.asyncio as redis
from src.config import settings


class UsersClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.USER_SERVICE_URL

    async def user_exists(self, user_id: UUID) -> bool:
        url = f"{self.base_url}/users/{user_id}"
        timeout = aiohttp.ClientTimeout(total=2)
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.get(url) as resp:
                return resp.status == 200


@dataclass(frozen=True, slots=True)
class FxQuote:
    base: str
    quote: str
    rate: Decimal
    amount_in: Decimal
    amount_out: Decimal
    provider: str
    as_of: datetime

class FxClient:
    def __init__(
        self,
        api_key: str = settings.FX_API_TOKEN,
        redis_url: str = settings.REDIS_URL,
        http_timeout_sec: float = 3.0,
    ) -> None:
        self.api_key = api_key.strip("/")
        self.http_timeout = aiohttp.ClientTimeout(total=http_timeout_sec)
        self.r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def _get_payload(self) -> Dict[str, Any]:
        cached = await self.r.get("fx:fixer:latest")
        if cached:
            return json.loads(cached)

        url = f"{settings.FX_BASE_URL}/latest?access_key={self.api_key}"
        async with aiohttp.ClientSession(timeout=self.http_timeout, trust_env=True) as sess:
            async with sess.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Fixer HTTP {resp.status}: {await resp.text()}")
                data = await resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Fixer error: {url}, {data} {data.get('error')}")

        ttl = 10
        await self.r.setex("fx:fixer:latest", ttl, json.dumps(data))
        return data

    @staticmethod
    def _as_of(date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    async def convert(
        self,
        *,
        base: str,
        quote: str,
        amount: Decimal,
    ) -> FxQuote:
        base, quote = base.upper(), quote.upper()

        if base == quote:
            now = datetime.now(timezone.utc)
            return FxQuote(base, quote, Decimal("1"), amount, amount, "fixer.io", now)

        payload = await self._get_payload()
        rates: Dict[str, float] = payload["rates"]
        as_of = self._as_of(payload["date"])

        if base not in rates or quote not in rates:
            raise RuntimeError(f"Missing rates for {base} or {quote}")
        rate = Decimal(str(rates[quote])) / Decimal(str(rates[base]))

        amount_out = amount * rate
        return FxQuote(base, quote, rate, amount, amount_out, "fixer.io", as_of)

