import asyncio
import json
import logging
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pandas import DataFrame
import pandas as pd
from processor import get_features
from config import Config

logger = logging.getLogger(__name__)

class FeatureEngineeringService:
    def __init__(self):
        self._nc: Client = Client()
        self._js: JetStreamContext
        self._config = Config()
        self._running = False
    
    async def ensure_consumer(self):
        try:
            logger.info(f"Checking consumer {self._config.consumer_name} exists...")
            await self._js.consumer_info(self._config.stream_name, self._config.consumer_name)
            logger.info(f"Consumer {self._config.consumer_name} already exists")
        except:
            logger.warning(f"Consumer did not exist. Configuring it now.")
            config = ConsumerConfig(
                    name=self._config.consumer_name, durable_name=self._config.consumer_name, deliver_policy=DeliverPolicy.NEW,
                    filter_subject=self._config.raw_subject, ack_policy=AckPolicy.EXPLICIT
                    )
            await self._js.add_consumer(self._config.stream_name, config)
            logger.warning(f"Consumer {self._config.consumer_name} created.")

    async def connect_nats(self):
        logger.info("Connecting to NATS...")
        await self._nc.connect(self._config.nats_url)
        self._js = self._nc.jetstream()
        logger.info("Connected")

    async def process_message(self, subject: str, data):
        coin_pair = subject.split(".")[-1]
        subject = f"{self._config.processed_subject}.{coin_pair}"
        logger.info(f"Raw data received for {coin_pair}...")
        try:

            ohlc_data: DataFrame = pd.DataFrame(json.loads(data))
            processed_data: str = get_features(ohlc_data)
            logger.info(f"Features generated... Publishing.")

            ack = await self._js.publish(
                    subject,
                    processed_data.encode("utf-8")
                    )
            logger.info(f"Data published [{ack}]")
        except Exception as e:
            logger.error(f"Failed to publish data to {subject}: {e}")

    async def start(self):
        await self.connect_nats()
        await self.ensure_consumer()
        self._running = True
        try:
            while self._running:
                await self.consume_messages()
        except asyncio.CancelledError:
            logger.info("FeatureService cancelled. Exiting task loop")
        finally:
            logger.info("FeatureEngineeringService finished")

    async def stop(self):
        self._running = False
        await self._nc.close()

    async def consume_messages(self):

        sub = await self._js.pull_subscribe(self._config.raw_subject, self._config.consumer_name)
        
        while self._running:
            try:
                msgs = await sub.fetch(1, timeout=5)
                for msg in msgs:
                    await self.process_message(msg.subject, msg.data.decode())
                    await msg.ack()
            except asyncio.TimeoutError:
                continue

