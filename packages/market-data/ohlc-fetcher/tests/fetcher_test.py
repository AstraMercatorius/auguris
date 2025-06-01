import asyncio
from datetime import datetime, timedelta
import unittest
from unittest.mock import AsyncMock, Mock, patch

from src.crontask import Crontask
from src.publisher import Publisher


mock_environ = {
    "API_KEY": "foo",
    "PRIVATE_KEY": "bar",
    "PAIRS": "FOO/USD",
    "NATS_URL": "nats://nats:4222",
    "CRON_SECONDS": "2",
    "NATS_SUBJECT": "market-data.raw"
}

mock_default_kraken_response = {
    "result": {
        "FOO/USD": [
            [1700000000, 50000, 505000, 49500, 50200, 1000, 1000, 1000]
            ]
    }
}

class TestFetcher(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock httpx_get
        self.patcher_httpx_get = patch("src.fetcher.httpx.AsyncClient.get", new_callable=AsyncMock)
        self.mock_httpx_get = self.patcher_httpx_get.start()

        # Mock datetime
        self.patcher_datetime = patch("src.fetcher.datetime")
        self.patcher_datetime_publisher = patch("src.publisher.fetcher.datetime")
        self.mock_datetime = self.patcher_datetime.start()
        self.mock_datetime_publisher = self.patcher_datetime_publisher.start()
        self.fixed_datetime = datetime.today()
        self.mock_datetime.today.return_value = self.fixed_datetime
        self.mock_datetime_publisher.today.return_value = self.fixed_datetime

        # Mock environ
        self.patcher_os_environ = patch.dict("os.environ", mock_environ)
        self.patcher_os_environ.start()

        # Mock NATS
        self.patcher_nats_connect = patch("src.publisher.nats.connect")
        self.mock_nats_connect = self.patcher_nats_connect.start()
        self.mock_nc = AsyncMock()
        self.mock_js = AsyncMock()
        self.mock_js.publish = AsyncMock()
        self.mock_nc.jetstream = Mock(return_value=self.mock_js)
        self.mock_nats_connect.return_value = self.mock_nc
        
    async def asyncTearDown(self):
        self.patcher_httpx_get.stop()
        self.patcher_datetime.stop()
        self.patcher_os_environ.stop()
        self.patcher_nats_connect.stop()

    def _set_httpx_get_response(self, api_body_response = mock_default_kraken_response):
        """
        Sets the response for any expected HTTP response
        """
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=api_body_response)
        self.mock_httpx_get.return_value = mock_response

    async def test_fetch_and_publish(self):
        self._set_httpx_get_response(mock_default_kraken_response)
        
        async def run_cron_short_time():
            try:
                await asyncio.wait_for(cron.start(), timeout=3.0)
            except asyncio.TimeoutError:
                pass

        cron = Crontask()
        cron.clear_subscribers()
        nats_publisher = Publisher(cron)
        await nats_publisher.start()
        await run_cron_short_time()

        assert cron is nats_publisher._cron
        
        interval = 15
        since = int((self.fixed_datetime - timedelta(minutes=interval * 100)).timestamp())
        self.mock_httpx_get.assert_called_with(
            f"https://api.kraken.com/0/public/OHLC?pair={mock_environ['PAIRS']}&interval={interval}&since={since}"
        )
        self.mock_nats_connect.assert_called_once_with(servers=[mock_environ["NATS_URL"]])
        expected_subject = f"{mock_environ['NATS_SUBJECT']}.FOO-USD"
        expected_pub_data = b'[{"Date":1699978400000,"Open":50000,"High":505000,"Low":49500,"Close":50200,"Volume":1000}]'
        self.mock_js.publish.assert_called_with(expected_subject, expected_pub_data)

    async def test_crontask_basic_functionality(self):
        cron1 = Crontask()
        cron2 = Crontask()
        cron1.set_interval(2)

        tasks = [
            asyncio.create_task(cron1.start()),
            asyncio.create_task(cron2.start())
        ]

        try:
            await asyncio.wait(tasks, timeout=3.0)
        except asyncio.TimeoutError:
            pass

        assert cron1 is cron2
        
        cron1.stop()
        cron1.clear_subscribers()

        mock_listener = AsyncMock()
        cron1.subscribe(mock_listener)
        
        try:
            await asyncio.wait_for(cron1.start(), timeout=3.0)
        except Exception:
            pass

        mock_listener.assert_called()
    
