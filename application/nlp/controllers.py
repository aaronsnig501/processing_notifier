from application.shared.redis.redis import Channel

from sanic import Blueprint
from sanic.log import logger

bp = Blueprint("nlp_notifier", url_prefix="/api")


@bp.websocket("/nlp/notifier/<channel_name>/<client_id>")
async def nlp_notifier(request, ws, channel_name, client_id):
    logger.info("Incoming WS request")
    channel, is_existing = await Channel.get(
        request.app.ctx.redis.pubsub(),
        request.app.ctx.redis,
        f"{channel_name}-{client_id}"
    )

    client = await channel.register(ws, client_id)

    if not is_existing:
        request.app.add_task(channel.receiver())

    try:
        await client.receiver()
    finally:
        await channel.unregister(client)