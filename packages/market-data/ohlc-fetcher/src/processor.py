from datetime import datetime
import pandas as pd
from pandas import DataFrame


def process_crypto_pair(raw_data) -> DataFrame:
    for ohlc in raw_data:
        ohlc[0] = datetime.fromtimestamp(ohlc[0])
    
    data_columns = ["Date", "Open", "High", "Low", "Close", "VWAP", "Volume", "Count"]
    ohlc_df = pd.DataFrame(raw_data, columns=pd.Index(data_columns))
    ohlc_df.drop(columns=["VWAP", "Count"], inplace=True)
    ohlc_df["Open"] = pd.to_numeric(ohlc_df["Open"], errors="coerce")
    ohlc_df["High"] = pd.to_numeric(ohlc_df["High"], errors="coerce")
    ohlc_df["Low"] = pd.to_numeric(ohlc_df["Low"], errors="coerce")
    ohlc_df["Close"] = pd.to_numeric(ohlc_df["Close"], errors="coerce")
    ohlc_df["Volume"] = pd.to_numeric(ohlc_df["Volume"], errors="coerce")

    return ohlc_df
