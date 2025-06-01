Feature: Fetch OHLC Data

  Scenario: Fetch BTC/USD data
    Given a request is made for "BTC/USD" data
    Then the raw data should be pushed in "market-data.raw.BTC-USD" subject
