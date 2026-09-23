"""Зашифрованное хранилище соответствий с TTL на каждой записи.

Если Redis недоступен, чтение и запись уходят в память процесса: маскирование
не останавливается, демаскирование работает для запросов, попавших в тот же
воркер, а деградация видна в метриках.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from collections import OrderedDict

import orjson
import redis
import structlog
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..observe.metrics import Metrics

log = structlog.get_logger()
_metrics = Metrics()

MEMORY_LIMIT = 200_000
DEGRADE_INTERVAL = 5.0
REDIS_ATTEMPTS = 2
_FAILED = object()


class Vault:
    """Зашифрованное хранилище маска -> оригинал."""

    def __init__(self, redis, key: bytes, prefix: str) -> None:
        self.redis = redis
        self.prefix = prefix
        self._aes = AESGCM(key)
        self._mac_key = hashlib.sha256(b"mac:" + key).digest()
        self._memory: OrderedDict[str, tuple[float, bytes]] = OrderedDict()
        self._last_warn = 0.0

    @property
    def backend(self) -> str:
        return "redis" if self.redis is not None else "memory"

    @classmethod
    async def create(cls, redis_url: str, vault_key: str, prefix: str) -> Vault:
        client = None
        if redis_url:
            client = redis.asyncio.Redis.from_url(
                redis_url,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
                max_connections=512,
                health_check_interval=30,
            )
        key = await cls._resolve_key(client, vault_key, prefix)
        return cls(client, key, prefix)

    @staticmethod
    async def _resolve_key(client, vault_key: str, prefix: str) -> bytes:
        if vault_key:
            try:
                key = base64.urlsafe_b64decode(vault_key)
            except ValueError as exc:
                raise ValueError(
                    "VAULT_KEY должен кодировать ровно 32 байта (urlsafe base64)"
                ) from exc
            if len(key) != 32:
                raise ValueError("VAULT_KEY должен кодировать ровно 32 байта (urlsafe base64)")
            return key
        if client is None:
            log.warning("vault.ephemeral_key")
            return secrets.token_bytes(32)
        candidate = secrets.token_bytes(32)
        addr = f"{prefix}:vault:bootstrap-key"
        try:
            await client.set(addr, base64.urlsafe_b64encode(candidate).decode(), nx=True)
            stored = await client.get(addr)
        except redis.exceptions.RedisError, OSError:
            stored = None
        if stored:
            key = base64.urlsafe_b64decode(stored)
            if len(key) != 32:
                key = candidate
        else:
            key = candidate
        log.warning("vault.bootstrap_key", note="ключ лежит в Redis")
        return key

    def digest(self, value: str) -> str:
        return hmac.new(self._mac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    def address(self, namespace: str, owner: str, identifier: str) -> str:
        return f"{self.prefix}:{namespace}:{owner}:{self.digest(identifier)[:40]}"

    def _encrypt(self, value: dict, address: str) -> bytes:
        nonce = secrets.token_bytes(12)
        data = orjson.dumps(value)
        ct = self._aes.encrypt(nonce, data, address.encode("utf-8"))
        return nonce + ct

    def _decrypt(self, blob: bytes, address: str) -> dict | None:
        try:
            nonce = blob[:12]
            ct = blob[12:]
            data = self._aes.decrypt(nonce, ct, address.encode("utf-8"))
            return orjson.loads(data)
        except InvalidTag, ValueError:
            return None

    async def _redis_call(self, operation: str, call):
        for attempt in range(REDIS_ATTEMPTS):
            try:
                return await call()
            except (redis.exceptions.RedisError, OSError) as e:
                if attempt == REDIS_ATTEMPTS - 1:
                    self._degrade(operation, e)
        return _FAILED

    async def get(self, address: str) -> dict | None:
        blob: bytes | None = None
        if self.redis is not None:
            result = await self._redis_call("get", lambda: self.redis.get(address))
            if result is not _FAILED:
                blob = result
        if blob is None and self._memory:
            entry = self._memory.get(address)
            if entry is not None:
                expiry, mem_blob = entry
                if expiry > time.monotonic():
                    blob = mem_blob
                else:
                    del self._memory[address]
        if blob is None:
            return None
        return self._decrypt(blob, address)

    async def put(self, address: str, value: dict, ttl: int, only_new: bool = False) -> bool:
        blob = self._encrypt(value, address)
        if self.redis is not None:
            ok = await self._redis_call(
                "put", lambda: self.redis.set(address, blob, ex=ttl, nx=only_new)
            )
            if ok is not _FAILED:
                return bool(ok) or not only_new
        return self._memory_put(address, blob, ttl, only_new)

    def _memory_put(self, address: str, blob: bytes, ttl: int, only_new: bool) -> bool:
        now = time.monotonic()
        if only_new and address in self._memory:
            expiry, _ = self._memory[address]
            if expiry > now:
                return False
        self._memory[address] = (now + ttl, blob)
        self._memory.move_to_end(address)
        while len(self._memory) > MEMORY_LIMIT:
            self._memory.popitem(last=False)
        return True

    async def delete(self, address: str) -> None:
        self._memory.pop(address, None)
        if self.redis is not None:
            try:
                await self.redis.delete(address)
            except (redis.exceptions.RedisError, OSError) as e:
                self._degrade("delete", e)

    async def ping(self) -> bool:
        if self.redis is None:
            return True
        try:
            return bool(await self.redis.ping())
        except redis.exceptions.RedisError, OSError:
            return False

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()

    def _degrade(self, operation: str, error: Exception) -> None:
        _metrics.degraded_total.labels(component="redis").inc()
        now = time.monotonic()
        if now - self._last_warn >= DEGRADE_INTERVAL:
            self._last_warn = now
            log.warning(
                "store.degraded",
                operation=operation,
                error=type(error).__name__,
                fallback="memory",
            )
