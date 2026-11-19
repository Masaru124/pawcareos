import logging
import os
import ssl
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

logger = logging.getLogger("pawcare.db")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def is_local_url(url: str) -> bool:
    return "localhost" in url or "127.0.0.1" in url


def ssl_context() -> ssl.SSLContext:
    """Verify against DB_CA_BUNDLE when given, otherwise encrypt without pinning the CA.

    Supabase's pooler serves a chain rooted in its own CA, which is not in the OS trust
    store, so verification fails out of the box. Set DB_CA_BUNDLE to the provider's
    certificate to get a verified connection.
    """
    bundle = os.environ.get("DB_CA_BUNDLE")
    if bundle:
        return ssl.create_default_context(cafile=bundle)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    logger.warning(
        "TLS to the hosted database is encrypted but not verified; set DB_CA_BUNDLE to pin the CA"
    )
    return context


def connect_args_for(url: str) -> dict:
    """A hosted database gets TLS; a transaction pooler cannot keep prepared statements."""
    if is_local_url(url):
        return {}
    return {
        "ssl": ssl_context(),
        "statement_cache_size": 0,
    }


def build_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True, connect_args=connect_args_for(url))


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = build_engine(get_settings().database_url)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """One transaction per request: commit when the handler returns, roll back when it raises."""
    async with get_sessionmaker()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
