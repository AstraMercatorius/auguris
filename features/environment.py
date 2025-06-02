import asyncio
import os
import json
import requests

from behave import fixture, use_fixture
from nats.aio.client import Client
from nats.js.api import AckPolicy, ConsumerConfig, StreamConfig

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
STREAM_NAME = os.getenv("STREAM_NAME", "market-data")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "feature-engineering")


def register_mock(json_filename, path, method="GET"):
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, json_filename)

    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Mock JSON not found: {json_path!r}")

    with open(json_path, "r", encoding="utf-8") as f:
        mock_response = json.load(f)

    payload = {
        "filters": {
            "path": path,
            "method": method
        },
        "response": {
            "body": mock_response
        }
    }

    url = "http://localhost:8000/mock"
    resp = requests.post(url, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to register mock for {method} {path}. "
            f"Status={resp.status_code}, Body={resp.text}"
        )

    return resp

def clear_mocks():
    url = "http://localhost:8000/mock"
    resp = requests.delete(url)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to clear mocks"
            f"Status={resp.status_code} Path={url} Method=DELETE"
        )

@fixture
def configure_mock_kraken(context):
    context.register_mock = register_mock
    yield context
    clear_mocks()

@fixture
def configure_nats(context):
    context.loop = asyncio.new_event_loop()
    context.nc = Client()

    context.loop.run_until_complete(context.nc.connect(NATS_URL))
    assert context.nc.is_connected, "Failed to connect to NATS"

    context.js = context.nc.jetstream()

    # stream_cfg = StreamConfig(name=STREAM_NAME, subjects=[f"{STREAM_NAME}.>"])
    # context.loop.run_until_complete(context.js.add_stream(config=stream_cfg))
    #
    consumer_cfg = ConsumerConfig(durable_name=f"{CONSUMER_NAME}_test", filter_subject=f"{STREAM_NAME}.raw.>", ack_policy=AckPolicy.EXPLICIT)
    context.loop.run_until_complete(
            context.js.add_consumer(STREAM_NAME, consumer_cfg)
            )

    yield context

    context.loop.run_until_complete(
            context.js.delete_consumer(STREAM_NAME, f"{CONSUMER_NAME}_test")
            )
    #
    # context.loop.run_until_complete(
    #         context.js.delete_stream(STREAM_NAME)
    #         )
    
    context.loop.run_until_complete(context.nc.drain())
    context.loop.run_until_complete(context.nc.close())

def before_all(context):
    use_fixture(configure_mock_kraken, context)
    use_fixture(configure_nats, context)
    pass
