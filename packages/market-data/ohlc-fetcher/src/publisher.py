import logging
import os
import nats
from nats.aio.client import Client
from nats.js import JetStreamContext
import pandas as pd

from crontask import Crontask
import fetcher
from processor import process_crypto_pair

logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, cron: Crontask):
        self._nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self._nats_subject = os.getenv("NATS_SUBJECT", "market-data.raw")
        self._pairs = os.getenv("PAIRS", "BTC/USD").split(",")
        self._nc: Client
        self._js: JetStreamContext
        self._cron = cron

    async def _connect_nats(self):
        self._nc = await nats.connect(servers=[self._nats_url])
        self._js = self._nc.jetstream()
        logger.info("Connected to NATS")

    async def _get_dataframe(self, pair: str) -> pd.DataFrame:
        raw_data = await fetcher.get_ohlc(pair)
        logger.info(f"Fetched data {len(raw_data)}")
        ohlc_df = process_crypto_pair(raw_data)
        return ohlc_df
    
    async def _process_request(self):
        for pair in self._pairs:
            logger.info(f"Processing pair {pair}")
            df = await self._get_dataframe(pair)
            logger.info(f"Got the data for {pair}")
            await self._publish(pair, df)
            logger.info(f"Publishing pair {pair}")

    async def _publish(self, pair: str, df: pd.DataFrame):
        subject = f"{self._nats_subject}.{pair.replace('/', '-')}"
        logger.info(f"PUBLISHING: {subject}")
        data = str(df.to_json(orient="records"))
        try:
            logger.warning(f"jetstream: {self._js}")
            ack = await self._js.publish(subject, data.encode("utf-8"))
            logger.info(f"Published data for {subject} [{ack}]")
        except Exception as e:
            logger.error(f"Failed to publish data to {subject}: {e}")

    async def start(self):
        await self._connect_nats()
        self._cron.subscribe(self._process_request)
