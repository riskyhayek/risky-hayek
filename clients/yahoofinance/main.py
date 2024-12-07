import yfinance as yf


class YahooFinanceClient:
    def __init__(self):
        pass

    def get_intraday_stock_data_yahoo(
        self, symbols, interval="5m", period="1d"
    ):
        # Convert single symbol to list for consistent handling
        if isinstance(symbols, str):
            symbols = [symbols]

        # Download the data
        df = yf.download(
            tickers=symbols.tolist(),
            interval=interval,
            period=period,
            group_by="ticker",
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


yahoo_finance_client = YahooFinanceClient()
