from clients.alphavantage import alphavantage_client
from clients.investments import investments_client
from clients.yahoofinance import yahoo_finance_client
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import requests
import json

URL_PIP = "https://www.piplatam.com/Home/filiales?country=MX"

_FUND_ID = 6
_CALENDAR = "XMEX"


class PerformanceAttribution:
    def __init__(self):
        self.start_date, self.end_date = (
            self.calculate_performance_attribution_date_range()
        )
        self.portfolio_df = investments_client.get_portfolio(fund_id=_FUND_ID)
        tickers = self.portfolio_df.index

        self.intraday_asset_prices = (
            yahoo_finance_client.get_intraday_stock_data_yahoo(symbols=tickers)
        )
        self.usdmxn_intraday_prices = (
            alphavantage_client.get_fx_intraday_alphavantage(
                from_symbol="USD", to_symbol="MXN"
            )
        )
        self.asset_daily_prices = (
            alphavantage_client.get_price_timeseries_alphavantage(
                tickers=tickers,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        )

        self.usdmxn_end, self.usdmxn_start = fetch_mxn_pip(self.end_date)

        if self.usdmxn_end is None:
            usdmxn_daily_prices = alphavantage_client.get_fx_daily_alphavantage(
                from_symbol="USD",
                to_symbol="MXN",
                start_date=self.start_date,
                end_date=self.end_date,
            )
            self.usdmxn_end = usdmxn_daily_prices.iloc[-1]["Close"]

        print("USDMXN Start: ", self.usdmxn_start)
        print("USDMXN End: ", self.usdmxn_end)

        self.intraday_portfolio_returns = (
            self.calculate_intraday_performance_attribution_serie()
        )

        self.attribution_df = self.calculate_performance_attribution()
        self.total_return_mxn = self.attribution_df["ctr_mxn"].sum()
        self.total_return_usd = self.attribution_df["ctr_usd"].sum()
        self.total_equity_effect = self.total_return_usd
        self.total_fx_effect = self.total_return_mxn - self.total_equity_effect

    def calculate_intraday_performance_attribution_serie(self):
        usdmxn_start = self.usdmxn_start
        usdmxn_end = self.usdmxn_end
        asset_prices_start = self.asset_daily_prices.iloc[0]
        asset_prices_end = self.asset_daily_prices.iloc[-1]
        asset_prices_start_mxn = asset_prices_start * usdmxn_start
        asset_prices_end_mxn = asset_prices_end * usdmxn_end

        # Convert both dataframes to CDMX timezone
        aligned_fx = self.usdmxn_intraday_prices.tz_localize("UTC").tz_convert(
            "America/Mexico_City"
        )
        if self.intraday_asset_prices.index.tz:
            aligned_assets = self.intraday_asset_prices.tz_convert(
                "America/Mexico_City"
            )
        else:
            aligned_assets = self.intraday_asset_prices.tz_localize(
                "UTC"
            ).tz_convert("America/Mexico_City")

        # Resample and align both dataframes to the same timestamp
        aligned_fx = aligned_fx.resample("5min").ffill()
        aligned_assets = aligned_assets.resample("5min").ffill()

        # Reindex FX data to match asset prices index
        aligned_fx = aligned_fx.reindex(aligned_assets.index, method="ffill")

        # Multiply each asset price by the corresponding FX rate
        intraday_asset_prices_mxn = aligned_assets.multiply(
            aligned_fx["Close"], axis=0
        )
        intraday_asset_prices_mxn.iloc[0] = asset_prices_start_mxn.reindex(
            intraday_asset_prices_mxn.columns
        )
        intraday_asset_prices_mxn.iloc[-1] = asset_prices_end_mxn.reindex(
            intraday_asset_prices_mxn.columns
        )

        intraday_asset_prices_mxn_returns = (
            intraday_asset_prices_mxn.pct_change()
        ).fillna(0.0)

        # Ensure weights and returns are aligned
        w = self.portfolio_df["weight"]
        aligned_returns = intraday_asset_prices_mxn_returns.reindex(
            columns=w.index
        )

        # Calculate portfolio returns (transpose aligned_returns)
        intraday_portfolio_returns = aligned_returns.mul(w).sum(axis=1)
        intraday_portfolio_returns = (
            1 + intraday_portfolio_returns
        ).cumprod() * 100 - 100

        return intraday_portfolio_returns

    def calculate_performance_attribution_date_range(self):
        """Calculate the start and end dates for the performance attribution."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        mexican_calendar = mcal.get_calendar(_CALENDAR)
        schedule = mexican_calendar.schedule(
            start_date=datetime.now() - timedelta(days=10),
            end_date=end_date,
        )
        start_date = schedule.index[-2].strftime("%Y-%m-%d")
        return start_date, end_date

    def calculate_performance_attribution(self):
        attribution_df = self.asset_daily_prices.T
        attribution_df = attribution_df.iloc[:, [0, -1]]
        attribution_df.columns = ["start_price", "end_price"]
        attribution_df["return_usd"] = (
            attribution_df["end_price"] / attribution_df["start_price"] - 1
        )
        usd_return = self.usdmxn_end / self.usdmxn_start - 1

        attribution_df["return_mxn"] = (1 + attribution_df["return_usd"]) * (
            1 + usd_return
        ) - 1

        attribution_df = self.portfolio_df.join(attribution_df, how="outer")
        attribution_df["ctr_mxn"] = (
            attribution_df["return_mxn"] * attribution_df["weight"]
        )
        attribution_df["ctr_usd"] = (
            attribution_df["return_usd"] * attribution_df["weight"]
        )
        attribution_df.index.name = "ticker"

        return attribution_df


def extract_date(string):
    date_string = string.split()[0]
    date = datetime.strptime(date_string, "%Y/%m/%d")
    return date.strftime("%Y-%m-%d")


def fetch_mxn_pip(date_today):
    str_start = "        renderTasaCambio("
    str_end = "        renderTasaInteres"
    str_next = "       renderTasaCambio("
    response = requests.get(URL_PIP)
    response = response.text
    response = response[response.find(str_start) + 1 : response.find(str_end)]
    response = response.replace(str_next, "")
    response = response[:-4]
    response = json.loads(response)
    response = response[0]
    pip_date = extract_date(response["txtBenchmark"])

    # depending on time, we get the las usd value
    if date_today == pip_date:
        usd_today = response["dblValue"]
        usd_yesterday = response["dblChange"]
    else:
        usd_today = None
        usd_yesterday = response["dblValue"]

    return usd_today, usd_yesterday
