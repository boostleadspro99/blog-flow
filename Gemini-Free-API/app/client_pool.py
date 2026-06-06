import asyncio
import logging
from typing import Dict, Optional

from gemini_webapi.client import GeminiClient

logger = logging.getLogger("client_pool")


class PooledClient:
    """Wraps a GeminiClient with lazy init and re-init support."""

    def __init__(
        self,
        user_id: str,
        secure_1psid: str,
        secure_1psidts: str,
        proxy: Optional[str] = None,
    ):
        self.user_id = user_id
        self.secure_1psid = secure_1psid
        self.secure_1psidts = secure_1psidts
        self.proxy = proxy
        self._client: Optional[GeminiClient] = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def get_client(self) -> GeminiClient:
        """Return initialized client, lazy-init on first call."""
        if self._client and self._initialized:
            return self._client
        async with self._init_lock:
            if self._client and self._initialized:
                return self._client
            return await self._do_init()

    async def _do_init(self) -> GeminiClient:
        """Create and initialize a new GeminiClient."""
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.debug(f"Non-critical: closing old GeminiClient failed: {e}")
        self._client = GeminiClient(
            secure_1psid=self.secure_1psid,
            secure_1psidts=self.secure_1psidts,
            proxy=self.proxy,
        )
        await self._client.init(auto_refresh=False)
        self._initialized = True
        logger.info(f"GeminiClient initialized for user {self.user_id}")
        return self._client

    async def reinit(self, new_1psid: str, new_1psidts: str) -> GeminiClient:
        """Reinitialize with new cookies (after user updates them)."""
        self.secure_1psid = new_1psid
        self.secure_1psidts = new_1psidts
        self._initialized = False
        return await self._do_init()

    async def close(self):
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.debug(f"Non-critical: closing GeminiClient failed: {e}")
        self._initialized = False


class GeminiClientPool:
    """Manages a pool of GeminiClients keyed by user_id."""

    def __init__(self, proxy: Optional[str] = None):
        self._pool: Dict[str, PooledClient] = {}
        self._proxy = proxy
        self._lock = asyncio.Lock()

    async def get_or_create(
        self, user_id: str, secure_1psid: str, secure_1psidts: str
    ) -> PooledClient:
        async with self._lock:
            if user_id in self._pool:
                existing = self._pool[user_id]
                if (
                    existing.secure_1psid != secure_1psid
                    or existing.secure_1psidts != secure_1psidts
                ):
                    logger.info(f"Cookies changed for user {user_id}, reinitializing...")
                    await existing.reinit(secure_1psid, secure_1psidts)
                return existing
            pooled = PooledClient(
                user_id, secure_1psid, secure_1psidts, self._proxy
            )
            self._pool[user_id] = pooled
            logger.info(
                f"Created new PooledClient for user {user_id} "
                f"(total active: {len(self._pool)})"
            )
            return pooled

    async def remove(self, user_id: str):
        async with self._lock:
            pooled = self._pool.pop(user_id, None)
            if pooled:
                await pooled.close()
                logger.info(f"Removed client for user {user_id}")

    async def close_all(self):
        async with self._lock:
            for pooled in self._pool.values():
                await pooled.close()
            self._pool.clear()

    def get_active_count(self) -> int:
        return len(self._pool)
