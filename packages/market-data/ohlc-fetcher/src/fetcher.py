from datetime import datetime, timedelta
import logging
import os
from typing import List
import httpx

logger = logging.getLogger(__name__)

async def get_ohlc(pair: str) -> List:
    base_url =  os.getenv("KRAKEN_URL", "https://api.kraken.com")
    interval = 15
    since = int((datetime.today() - timedelta(minutes=interval * 100)).timestamp())
    api_path = "0/public/OHLC"
    api_data = f"pair={pair}&interval={interval}&since={since}"
    url = f"{base_url}/{api_path}?{api_data}"
    async with httpx.AsyncClient() as client:
        logger.info("Requesting data...")
        response = await client.get(url)
        logger.info(f"Got response: {response}")
        raw_data = response.json()
        result = raw_data['result'][pair]
        return result
