from app.db import build_engine, connect_args_for, is_local_url

REMOTE = "postgresql+asyncpg://user:secret@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"


def test_a_local_url_gets_no_extra_arguments() -> None:
    assert connect_args_for("postgresql+asyncpg://postgres:pawcare@localhost:5433/pawcare") == {}
    assert is_local_url("postgresql+asyncpg://postgres:pawcare@127.0.0.1:5433/pawcare")


def test_a_hosted_url_gets_tls_and_no_statement_cache() -> None:
    options = connect_args_for(REMOTE)
    assert options["ssl"] is not None
    assert options["statement_cache_size"] == 0


def test_a_hosted_url_builds_an_engine() -> None:
    """The arguments must survive create_async_engine, not just the dict lookup."""
    engine = build_engine(REMOTE)
    assert engine is not None
