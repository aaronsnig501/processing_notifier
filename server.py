from sanic import Sanic
from redis.asyncio import Redis as RedisPy
from application.nlp.controllers import bp as nlp_notifier_bp

app = Sanic("processing_notifier")

app.blueprint(nlp_notifier_bp)

redis_connection = RedisPy.from_url("redis://redis:6379")

@app.listener("before_server_start")
async def redis_setup(app, loop):
    app.ctx.redis = redis_connection
