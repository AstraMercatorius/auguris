from datetime import datetime
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch
import pandas as pd

from pandas import DataFrame
from src.processor import get_features
from src.market_events import market_events

mock_environ = {
        "NATS_URL": "nats://nats:4222",
        "STREAM_NAME": "market-data",
        "CONSUMER_NAME": "feature-engineering",
        "RAW_SUBJECT": "market-data.raw.>",
        "PROCESSED_SUBJECT": "market-data.processed"
    }

def get_raw_mock_data() -> DataFrame:
    with open("mock_raw_data.json", 'r') as f:
        data = json.load(f)
        ohlc_data = data['result']['BTC/USD']
        for ohlc in ohlc_data:
            ohlc[0] = datetime.fromtimestamp(ohlc[0])

        data_columns = ["Date", "Open", "High", "Low", "Close", "VWAP", "Volume", "Count"]
        ohlc_df = pd.DataFrame(ohlc_data, columns=pd.Index(data_columns))
        ohlc_df.drop(columns=["VWAP", "Count"], inplace=True)
        ohlc_df["Open"] = pd.to_numeric(ohlc_df["Open"], errors="coerce")
        ohlc_df["High"] = pd.to_numeric(ohlc_df["High"], errors="coerce")
        ohlc_df["Low"] = pd.to_numeric(ohlc_df["Low"], errors="coerce")
        ohlc_df["Close"] = pd.to_numeric(ohlc_df["Close"], errors="coerce")
        ohlc_df["Volume"] = pd.to_numeric(ohlc_df["Volume"], errors="coerce")

        return ohlc_df

class TestFeatureEngineering(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock environ
        self.patcher_os_environ = patch.dict("os.environ", mock_environ)
        self.patcher_os_environ.start()

        self.patcher_nats_connect = patch("src.processor.publisher.nats.connect")
        self.mock_nats_connect = self.patcher_nats_connect.start()
        self.mock_nc = AsyncMock()
        self.mock_js = AsyncMock()
        self.mock_js.publish = AsyncMock()
        self.mock_nc.jetstream = Mock(return_value=self.mock_js)
        self.mock_nats_connect.return_value = self.mock_nc
        

    async def asyncTearDown(self):
        self.patcher_os_environ.stop()
        self.patcher_nats_connect.stop()

    async def test_process_raw_data(self):
        coin_pair = 'FOO-USD'
        mock_raw_data: DataFrame = get_raw_mock_data()
        
        mock_processed_event_called = Mock()
        market_events.on_processed += mock_processed_event_called
        market_events.on_raw_received += get_features
        
        market_events.on_raw_received(coin_pair, mock_raw_data)
        
        print(f"Called args: {mock_processed_event_called.call_args}")
        self.mock_nats_connect.assert_called_once_with(servers=[mock_environ["NATS_URL"]])
        self.mock_js.publish.assert_called_once()
