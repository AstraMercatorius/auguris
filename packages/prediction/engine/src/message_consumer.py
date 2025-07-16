import asyncio
import json
import logging
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from numpy.typing import NDArray
from pandas import DataFrame
import pandas as pd

from inference import InferenceEngine

logger = logging.getLogger(__name__)

class NATSMessageConsumer:
    def __init__(self, nats_server: str, stream_name: str, subject: str, consumer_name: str, prediction_stream_name: str, prediction_subject: str, engine: InferenceEngine):
        self.nc = Client()
        self.js: JetStreamContext
        self.nats_server = nats_server
        self.stream_name = stream_name
        self.subject = subject
        self.consumer_name = consumer_name
        self.prediction_stream_name = prediction_stream_name
        self.prediction_subject = prediction_subject
        self.engine = engine

    async def ensure_consumer(self):
        try:
            await self.js.consumer_info(self.stream_name, self.consumer_name)
        except:
            config = ConsumerConfig(
                    name=self.consumer_name, durable_name=self.consumer_name, deliver_policy=DeliverPolicy.NEW,
                    filter_subject=self.subject, ack_policy=AckPolicy.EXPLICIT
                    )
            await self.js.add_consumer(self.stream_name, config)

    async def connect_nats(self):
        await self.nc.connect(self.nats_server)
        self.js = self.nc.jetstream()

    async def send_prediction(self, predictions: NDArray, coin_pair: str):
        data = str(predictions)
        subject = f"{self.prediction_subject}.{coin_pair.replace('/', '-')}"
        ack = await self.js.publish(subject, data.encode("utf-8"))
        logger.info(f"Prediction published to {subject} [{ack}]")

    async def process_message(self, msg: Msg):
        try:
            subject = msg.subject
            data = msg.data.decode()
            coin_pair = subject.split(".")[-1]
            df: DataFrame = pd.DataFrame(json.loads(data))
            if df.empty:
                logger.warning(f"Empty message received for coin pair {coin_pair}")
                await msg.ack()
                return
            predictions = await self.engine.predict(df)
            await self.send_prediction(predictions[0], coin_pair)
            await msg.ack()
        except Exception as e:
            raise e
    
    async def consume_messages(self):
        await self.connect_nats()
        await self.ensure_consumer()

        sub = await self.js.pull_subscribe(self.subject, self.consumer_name)

        while True:
            try:
                [await self.process_message(msg) for msg in await sub.fetch(1, timeout=5)]
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("Cancelling message consumption...")
                await self.nc.close()
                return
