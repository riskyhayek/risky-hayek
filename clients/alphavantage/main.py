import pandas as pd
import requests
from settings import AlphaVantageClientSettings


class AlphaVantageClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_price_timeseries_alphavantage(self, tickers, start_date, end_date):
        all_data = {}
        for ticker in tickers:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={self.api_key}&entitlement=delayed"
            response = requests.get(url)
            data = response.json()
            if "Time Series (Daily)" in data:
                df = pd.DataFrame.from_dict(
                    data["Time Series (Daily)"], orient="index"
                )
                df.index = pd.to_datetime(df.index)
                df = df.rename(columns={"5. adjusted close": "Close"})
                df = df.sort_index()  # Ensure the index is sorted
                df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
                all_data[ticker] = df["Close"]

        if all_data:
            return pd.DataFrame(all_data).astype(float)
        else:
            print(
                "Failed to fetch data or no data available for the given tickers and date range"
            )
            return None

    def get_fx_intraday_alphavantage(
        self, from_symbol, to_symbol, interval="15min"
    ):
        url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&outputsize=full&from_symbol={from_symbol}&to_symbol={to_symbol}&interval={interval}&apikey={self.api_key}&entitlement=delayed"
        response = requests.get(url)
        data = response.json()
        if "Time Series FX (" + interval + ")" in data:
            df = pd.DataFrame.from_dict(
                data["Time Series FX (" + interval + ")"], orient="index"
            )
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={"4. close": "Close"})
            return df[["Close"]].astype(float)
        else:
            print("Failed to fetch data or no data available for USDMXN")
            return None

    def get_fx_daily_alphavantage(
        self, from_symbol, to_symbol, start_date, end_date
    ):
        url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={self.api_key}&entitlement=delayed"
        response = requests.get(url)
        data = response.json()
        if "Time Series FX (Daily)" in data:
            df = pd.DataFrame.from_dict(
                data["Time Series FX (Daily)"], orient="index"
            )
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={"4. close": "Close"})
            df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
            df = df.sort_index()
            return df[["Close"]].astype(float)
        else:
            print("Failed to fetch data or no data available for the FX pair")
            return None


alphavantage_client = AlphaVantageClient(
    api_key=AlphaVantageClientSettings.load_from_env_vars().alphavantage_api_key.get_secret_value()
)
