"""Report what a database URL reaches: driver, host, reachability and tables."""

import asyncio
import sys

import asyncpg

from app.config import get_settings
from app.db import is_local_url, ssl_context


def describe(url: str) -> str:
    host = url.rsplit("@", 1)[-1]
    return f"{url.split('://')[0]} -> {host}"


async def main(url: str) -> int:
    print("url:", describe(url))
    plain = url.replace("postgresql+asyncpg://", "postgresql://")
    options: dict = {"timeout": 20}
    if not is_local_url(url):
        options["ssl"] = ssl_context()

    try:
        connection = await asyncio.wait_for(asyncpg.connect(plain, **options), timeout=35)
    except (OSError, ValueError, TimeoutError, asyncpg.PostgresError) as exc:
        print("connect failed:", type(exc).__name__, str(exc)[:200])
        return 1

    try:
        rows = await connection.fetch(
            "select tablename from pg_tables where schemaname='public' order by tablename"
        )
        names = [row["tablename"] for row in rows]
        print(f"public tables: {len(names)}")
        for name in names:
            print("  -", name)
    finally:
        await connection.close()
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else get_settings().database_url
    raise SystemExit(asyncio.run(main(target)))
