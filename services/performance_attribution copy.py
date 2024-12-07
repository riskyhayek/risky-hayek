import pandas as pd
import yfinance as yf
import requests
from clients.alphavantage import alphavantage_client


def get_intraday_stock_data_yahoo(symbols, interval, period="1d"):
    """
    Fetch intraday stock data from Yahoo Finance and return it as a DataFrame.

    Parameters:
    - symbols (str or list): Single stock symbol or list of symbols (e.g., 'AAPL' or ['AAPL', 'MSFT']).
    - interval (str): Time interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h').
    - period (str): Data period (e.g., '1d', '7d', '60d', '730d'). Default is '1d'.

    Returns:
    - DataFrame: Multi-index DataFrame with (datetime, symbol) if multiple symbols,
                or simple DataFrame if single symbol.
    """
    # Convert single symbol to list for consistent handling
    if isinstance(symbols, str):
        symbols = [symbols]

    # Download the data
    df = yf.download(
        tickers=symbols, interval=interval, period=period, group_by="ticker"
    )

    if not df.empty:
        if len(symbols) == 1:
            return df["Close"]  # Return only Close column for single symbol
        else:
            # Restructure and pivot so tickers become columns
            return df.stack(level=0)[
                "Close"
            ].unstack()  # Add unstack() to pivot
    else:
        print(f"Failed to fetch data or no data available for {symbols}")
        return None


def get_usdmxn_intraday_alphavantage(api_key, interval="1min"):
    """
    Fetch USDMXN intraday data from Alpha Vantage and return only the 'Close' prices as a DataFrame.

    Parameters:
    - api_key (str): Your Alpha Vantage API key.
    - interval (str): Time interval (e.g., '1min', '5min', '15min', '30min', '60min'). Default is '1min'.

    Returns:
    - DataFrame: DataFrame with datetime index and 'Close' USDMXN exchange rate.
    """
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=USD&to_symbol=MXN&interval={interval}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if "Time Series FX (" + interval + ")" in data:
        df = pd.DataFrame.from_dict(
            data["Time Series FX (" + interval + ")"], orient="index"
        )
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={"4. close": "Close"})
        return df[["Close"]]
    else:
        print("Failed to fetch data or no data available for USDMXN")
        return None


def get_stock_timeseries_alphavantage(api_key, tickers, start_date, end_date):
    """
    Fetch daily stock data from Alpha Vantage for given tickers and date range.

    Parameters:
    - api_key (str): Your Alpha Vantage API key.
    - tickers (list): List of stock symbols (e.g., ['AAPL', 'MSFT']).
    - start_date (str): Start date in 'YYYY-MM-DD' format.
    - end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
    - DataFrame: DataFrame with date index and columns for each ticker's 'Close' price.
    """
    all_data = {}
    for ticker in tickers:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={api_key}"
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
        return pd.DataFrame(all_data)
    else:
        print(
            "Failed to fetch data or no data available for the given tickers and date range"
        )
        return None


# Example usage:
# df_yahoo = get_intraday_stock_data_yahoo(["AAPL", "MSFT", "GOOGL"], "5m")
# print(df_yahoo)

# api_key = "GV8EMBXNJ3MRSI5O"
# df_usdmxn = get_usdmxn_intraday_alphavantage(api_key, "5min")
# print(df_usdmxn)

"""
df_prices_av = get_stock_timeseries_alphavantage(
    api_key,
    tickers=["AAPL", "MSFT"],
    start_date="2024-12-04",
    end_date="2024-12-05",
)
"""
# print(df_prices_av)
