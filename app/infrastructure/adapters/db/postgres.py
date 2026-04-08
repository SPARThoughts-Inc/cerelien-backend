import asyncpg

from app.core.config import settings


class DatabaseAdapter:
    """Async PostgreSQL adapter using asyncpg connection pool."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create the asyncpg connection pool."""
        if self._pool is not None:
            return
        self._pool = await asyncpg.create_pool(
            dsn=settings.neon_database_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("DatabaseAdapter is not connected. Call connect() first.")
        return self._pool

    async def fetch_one(self, query: str, *args) -> dict | None:
        """Execute a query and return a single row as a dict, or None."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> list[dict]:
        """Execute a query and return all rows as a list of dicts."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(r) for r in rows]

    async def execute(self, query: str, *args) -> str:
        """Execute a single statement (INSERT, UPDATE, DELETE, DDL)."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def execute_many(self, query: str, args_list: list[tuple]) -> None:
        """Execute a statement for each set of args in args_list."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.executemany(query, args_list)
