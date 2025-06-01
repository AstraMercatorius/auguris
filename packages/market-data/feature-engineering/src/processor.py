import logging
import numpy as np
from pandas import DataFrame

from ta_features import add_timely_data, compute_oscillators, find_patterns

logger = logging.getLogger(__name__)

def get_features(ohlc_data: DataFrame) -> str:
    result = compute_oscillators(ohlc_data)
    result = find_patterns(result)
    result = add_timely_data(result)
    result.set_index("Date", inplace=True)
    result.replace([np.inf, -np.inf], np.nan, inplace=True)
    result.dropna(inplace=True)
    
    result = result.drop(columns=["Open", "High", "Low", "Close", "Volume"])
    processed_data = str(result.to_json(orient="records"))
    
    return processed_data
