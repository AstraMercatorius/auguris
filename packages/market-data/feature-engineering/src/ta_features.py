from pandas import DataFrame
import pandas as pd
import numpy as np
import talib

BUY = -1
HOLD = 0
SELL = 1

def compute_oscillators(data) -> DataFrame:
    log_return = np.log(data['Close']) - np.log(data['Close'].shift(1))
    data['Z_score'] = (((log_return - log_return.rolling(20).mean()) / log_return.rolling(20).std()))
    data['RSI'] = ((talib.RSI(data['Close'])) / 100)
    upper_band, _, lower_band = talib.BBANDS(data['Close'], nbdevup=2, nbdevdn=2, matype=talib._ta_lib.MA_Type.SMA)
    data['boll'] = ((data['Close'] - lower_band) / (upper_band - lower_band))
    data['ULTOSC'] = ((talib.ULTOSC(data['High'], data['Low'], data['Close'])) / 100)
    data['pct_change'] = (data['Close'].pct_change())
    data['zsVol'] = (data['Volume'] - data['Volume'].mean()) / data['Volume'].std()
    data['PR_MA_Ratio_short'] = ((data['Close'] - talib.SMA(data['Close'], 21)) / talib.SMA(data['Close'], 21))
    data['MA_Ratio_short'] = ((talib.SMA(data['Close'], 21) - talib.SMA(data['Close'], 50)) / talib.SMA(data['Close'], 50))
    data['MA_Ratio'] = (
                (talib.SMA(data['Close'], 50) - talib.SMA(data['Close'], 100)) / talib.SMA(data['Close'], 100))
    data['PR_MA_Ratio'] = ((data['Close'] - talib.SMA(data['Close'], 50)) / talib.SMA(data['Close'], 50))

    return data

def add_timely_data(data) -> DataFrame:
    data['DayOfWeek'] = pd.to_datetime(data['Date']).dt.dayofweek
    data['Month'] = pd.to_datetime(data['Date']).dt.month
    data['Hourly'] = pd.to_datetime(data['Date']).dt.hour / 4
    return data

def assign_labels(data, backward_window, forward_window, alpha, beta):
    data_copy = data.copy()
    data_copy['Close_MA'] = data_copy['Close'].ewm(span=backward_window).mean()
    data_copy['s-1'] = data_copy['Close'].shift(-forward_window)
    data_copy['alpha'] = alpha
    data_copy['beta'] = beta * (1 + (forward_window * 0.1))
    data_copy['label'] = data_copy.apply(check_label, axis=1)
    return data_copy['label']

def check_label(row):
    price_diff_ratio = abs((row['s-1'] - row['Close_MA']) / row['Close_MA'])
    within_alpha_beta = row['alpha'] < price_diff_ratio < row['beta']
    
    if not within_alpha_beta:
        return HOLD

    if row['s-1'] > row['Close_MA']:
        return SELL
    elif row['s-1'] < row['Close_MA']:
        return BUY
    else:
        return HOLD

def find_patterns(x) -> DataFrame:
    x['CDL2CROWS'] = talib.CDL2CROWS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDL3BLACKCROWS'] = talib.CDL3BLACKCROWS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDL3WHITESOLDIERS'] = talib.CDL3WHITESOLDIERS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLABANDONEDBABY'] = talib.CDLABANDONEDBABY(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLBELTHOLD'] = talib.CDLBELTHOLD(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLCOUNTERATTACK'] = talib.CDLCOUNTERATTACK(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLDARKCLOUDCOVER'] = talib.CDLDARKCLOUDCOVER(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLDRAGONFLYDOJI'] = talib.CDLDRAGONFLYDOJI(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLENGULFING'] = talib.CDLENGULFING(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLEVENINGDOJISTAR'] = talib.CDLEVENINGDOJISTAR(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLEVENINGSTAR'] = talib.CDLEVENINGSTAR(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLGRAVESTONEDOJI'] = talib.CDLGRAVESTONEDOJI(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLHANGINGMAN'] = talib.CDLHANGINGMAN(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLHARAMICROSS'] = talib.CDLHARAMICROSS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLINVERTEDHAMMER'] = talib.CDLINVERTEDHAMMER(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLMARUBOZU'] = talib.CDLMARUBOZU(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLMORNINGDOJISTAR'] = talib.CDLMORNINGDOJISTAR(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLMORNINGSTAR'] = talib.CDLMORNINGSTAR(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLPIERCING'] = talib.CDLPIERCING(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLRISEFALL3METHODS'] = talib.CDLRISEFALL3METHODS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLSHOOTINGSTAR'] = talib.CDLSHOOTINGSTAR(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLSPINNINGTOP'] = talib.CDLSPINNINGTOP(x['Open'], x['High'], x['Low'], x['Close']) / 100
    x['CDLUPSIDEGAP2CROWS'] = talib.CDLUPSIDEGAP2CROWS(x['Open'], x['High'], x['Low'], x['Close']) / 100
    return x
