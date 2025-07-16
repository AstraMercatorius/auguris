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

from config import Config
from inference import InferenceEngine


_logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self) -> None:
        self._nc: Client = Client()
        self._js: JetStreamContext
        self._config = Config()
        self._running = False
        self._engine: InferenceEngine = InferenceEngine()

    async def start(self):
        await self.__connect_nats()
        await self.__ensure_consumer()
        self._running = True

        try:
            while self._running:
                await self.__consume_messages()
        except asyncio.CancelledError:
            _logger.info("Service cancelled. Exiting task loop")
            await self.stop()
        finally:
            _logger.info("Service finished.")

    async def stop(self):
        self._running = False
        await self._nc.close()

    async def __connect_nats(self):
        _logger.info("Connecting to NATS...")
        await self._nc.connect(self._config.nats_url)
        self._js = self._nc.jetstream()
        _logger.info("Connected")

    async def __ensure_consumer(self):
        try:
            _logger.info(f"Checking consumer {self._config.consumer_name}")
            await self._js.consumer_info(self._config.stream_name, self._config.consumer_name)
        except:
            _logger.warning(f"Consumer did not exist. Configuring it now.")
            consumerConfig = ConsumerConfig(
                    name=self._config.consumer_name, durable_name=self._config.consumer_name,
                    deliver_policy=DeliverPolicy.NEW, filter_subject=self._config.raw_subject,
                    ack_policy=AckPolicy.EXPLICIT
            )
            await self._js.add_consumer(self._config.stream_name, consumerConfig)
            _logger.info(f"Consumer {self._config.consumer_name} created.")

    async def __consume_messages(self):
        sub = await self._js.pull_subscribe(self._config.raw_subject, self._config.consumer_name)
        while self._running:
            try:
                msgs = await sub.fetch(1, timeout=5)
                for msg in msgs:
                    await self.__process_message(msg)
            except asyncio.TimeoutError:
                continue

    async def __process_message(self, msg: Msg):
        subject = msg.subject
        data = msg.data.decode()
        coin_pair = subject.split(".")[-1]
        df: DataFrame = pd.DataFrame(json.loads(data))

        if df.empty:
            _logger.warning(f"Empty message received for {coin_pair}")
            await msg.ack()
            return

        try:
            predictions: NDArray = await self._engine.predict(df)
            await self.__send_prediction(predictions[0], coin_pair)
            await msg.ack()
        except Exception as e:
            _logger.error(f"Error occurred trying to process prediction for {coin_pair}. Exception: {e}")
            await msg.nak()

    async def __send_prediction(self, predictions: NDArray, coin_pair: str):
        data = str(predictions)
        subject = f"{self._config.prediction_subject}.{coin_pair.replace('/', '-')}"
        ack = await self._js.publish(subject, data.encode("utf-8"))
        _logger.info(f"Prediction published to {subject} [{ack}]")
