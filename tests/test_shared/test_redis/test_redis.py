from typing import Any
from unittest.mock import create_autospec
from uuid import uuid4
from pytest import mark
from redis.asyncio import Redis as AyncRedis
from redis.asyncio.client import PubSub

from application.shared.redis.redis import Channel


class TestRedis:

    @mark.asyncio
    async def test_get_not_already_existing(mocker: Any) -> None:
        mock_redis = create_autospec(AyncRedis)
        mock_pubsub = create_autospec(PubSub)
        name = f"nlp-{uuid4()}"

        channel, is_existing = await Channel.get(mock_pubsub, mock_redis, name)

        assert not is_existing
        assert channel.name == name
        mock_pubsub.subscribe.assert_awaited_with(name)
        assert len(channel.cache) == 1
        del channel.cache[name]

    @mark.asyncio
    async def test_get_already_existing(mocker: Any) -> None:
        mock_redis = create_autospec(AyncRedis)
        mock_pubsub = create_autospec(PubSub)
        name = f"nlp-{uuid4()}"

        await Channel.get(mock_pubsub, mock_redis, name)

        channel, is_existing = await Channel.get(mock_pubsub, mock_redis, name)

        assert is_existing
        assert channel.name == name
        assert len(channel.cache) == 1
        del channel.cache[name]
