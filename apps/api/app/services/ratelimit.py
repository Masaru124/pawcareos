import time

_buckets: dict[str, list[float]] = {}


def allow(key: str, *, limit: int = 20, window_seconds: int = 60) -> bool:
    """In-process only: enough to blunt a webhook retry storm, not a security control."""
    now = time.monotonic()
    hits = [stamp for stamp in _buckets.get(key, []) if now - stamp < window_seconds]
    if len(hits) >= limit:
        _buckets[key] = hits
        return False
    hits.append(now)
    _buckets[key] = hits
    return True


def reset() -> None:
    _buckets.clear()
