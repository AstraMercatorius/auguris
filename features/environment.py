import asyncio
import os

from behave import fixture, use_fixture
from nats.aio.client import Client
from nats.js.api import AckPolicy, ConsumerConfig, StorageType, StreamConfig

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
STREAM_NAME = os.getenv("STREAM_NAME", "market-data")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "feature-engineering")


@fixture
def configure_nats(context):
    context.loop = asyncio.new_event_loop()
    context.nc = Client()

    context.loop.run_until_complete(context.nc.connect(NATS_URL))
    assert context.nc.is_connected, "Failed to connect to NATS"

    context.js = context.nc.jetstream()

    stream_cfg = StreamConfig(name=STREAM_NAME, subjects=[f"{STREAM_NAME}.>"], storage=StorageType.MEMORY)
    context.loop.run_until_complete(context.js.add_stream(config=stream_cfg))

    consumer_cfg = ConsumerConfig(durable_name=CONSUMER_NAME, filter_subject=f"{STREAM_NAME}.raw.>", ack_policy=AckPolicy.EXPLICIT)
    context.loop.run_until_complete(
            context.js.add_consumer(STREAM_NAME, consumer_cfg)
            )

    yield context

    context.loop.run_until_complete(
            context.js.delete_consumer(STREAM_NAME, CONSUMER_NAME)
            )

    context.loop.run_until_complete(
            context.js.delete_stream(STREAM_NAME)
            )
    
    context.loop.run_until_complete(context.nc.drain())
    context.loop.run_until_complete(context.nc.close())

@fixture
def setup_foo(context):
    context.foo = "bar"
    yield context.foo
    context.foo = None

def before_all(context):
    use_fixture(setup_foo, context)
    use_fixture(configure_nats, context)
    pass
