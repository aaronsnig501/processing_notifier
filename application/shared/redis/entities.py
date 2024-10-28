from dataclasses import dataclass, field
from uuid import uuid4, UUID
from redis.asyncio import Redis
from sanic.server.websockets.impl import WebsocketImplProtocol


@dataclass
class Client:
    protocol: WebsocketImplProtocol
    redis: Redis
    channel_name: str
    uid: UUID = field(default_factory=uuid4)

    def __hash__(self) -> int:
        return self.uid.int

    async def receiver(self) -> None:
        """Receiver

        Websocket receive message handler. No messages are expected from the client so
        don't process anything received
        """
        while True:
            await self.protocol.recv()

    async def shutdown(self) -> None:
        """Shutdown

        Close the websocket connection
        """
        await self.protocol.close()


class ChannelCache(dict):
    ...