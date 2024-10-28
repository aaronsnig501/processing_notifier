from typing import Self
from uuid import UUID

from redis import PubSubError
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from sanic.server.websockets.impl import WebsocketImplProtocol
from sanic.log import logger

from .entities import Client, ChannelCache


class Channel:

    cache = ChannelCache()

    def __init__(self, pubsub: PubSub, redis: Redis, name: str) -> None:
        self.pubsub = pubsub
        self.redis = redis
        self.name = name
        self.clients: set[Client] = set()

    @classmethod
    async def get(cls, pubsub: PubSub, redis: Redis, name: str) -> tuple[Self, bool]:
        """Get

        Check the cache to see if the client already exists. If it does, retrieve and
        return it. Otherwise, instantiate a new client and subscribe to the pubsub
        channel and return the channel

        Args:
            pubsub (PubSub): The global PubSub instance
            redis (Redis): The global Redis instance
            name (str): The name of the channel

        Returns:
            tuple[Self, bool]:  Returns a channel instance and the `is_existing` flag to
                                indicate if the channel already exists
        """
        is_existing = False

        if name in cls.cache:
            channel = cls.cache[name]
            is_existing = True
        else:
            channel = cls(pubsub=pubsub, redis=redis, name=name)
            cls.cache[name] = channel
            await pubsub.subscribe(name)
        return channel, is_existing

    async def receiver(self) -> None:
        """Receiver

        Listens for any messages dropped onto the pubsub channel and send them to any
        websocket listeners
        """
        while True:
            try:
                raw = await self.pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
            except PubSubError:
                logger.error(f"PUBSUB closed <{self.name}>", exc_info=True)
                break
            else:
                if raw:
                    for client in self.clients:
                        await client.protocol.send(raw["data"])

    async def register(self, protocol: WebsocketImplProtocol, client_id: str) -> Client:
        """Register client

        Create a new client and add it to the channel cache

        Args:
            protocol (WebsocketImplProtocol): The websocket connection
            client_id (str): The ID of the client

        Returns:
            Client: The newly created client
        """
        client = Client(
            protocol=protocol,
            redis=self.redis,
            channel_name=self.name,
            uid=UUID(client_id)
        )
        self.clients.add(client)
        return client

    async def unregister(self, client: Client) -> None:
        """Unregister client

        Remove a client from the channel cache. Destroy if cache is empty

        Args:
            client (Client): The client to remove
        """
        if client in self.clients:
            await client.shutdown()
            self.clients.remove(client)

        if not self.clients:
            await self.destroy()

    async def destroy(self) -> None:
        """Destroy channel

        Delete the channel cache and reset the pubsub connection
        """
        del self.__class__.cache[self.name]
        await self.pubsub.reset()
