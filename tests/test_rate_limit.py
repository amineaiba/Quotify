import uuid

from redis.exceptions import RedisError

from app.core import rate_limit


class FakeRedis:
    def __init__(self, raise_error: bool = False) -> None:
        self._counts: dict[str, int] = {}
        self._raise_error = raise_error
        self.expired: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        if self._raise_error:
            raise RedisError("connection refused")
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expired[key] = seconds


async def test_allows_under_the_cap(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: fake)
    conversation_id = uuid.uuid4()

    for _ in range(10):  # default cap is 10/hour
        assert await rate_limit.is_rate_limited(conversation_id) is False


async def test_blocks_over_the_cap(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: fake)
    conversation_id = uuid.uuid4()
    for _ in range(10):
        await rate_limit.is_rate_limited(conversation_id)

    assert await rate_limit.is_rate_limited(conversation_id) is True


async def test_sets_expiry_on_first_hit(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: fake)
    conversation_id = uuid.uuid4()

    await rate_limit.is_rate_limited(conversation_id)

    key = f"ratelimit:conversation:{conversation_id}"
    assert fake.expired[key] == rate_limit.RATE_LIMIT_WINDOW_SECONDS


async def test_fails_open_when_redis_unreachable(monkeypatch):
    fake = FakeRedis(raise_error=True)
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: fake)

    assert await rate_limit.is_rate_limited(uuid.uuid4()) is False
