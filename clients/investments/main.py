import requests
import pandas as pd
from settings import InvestmentsAPISettings


class InvestmentsClient:
    def __init__(self):
        pass

    def get_portfolio(self, fund_id):
        url = InvestmentsAPISettings.load_from_env_vars().investments_api_url.get_secret_value() + str(
            fund_id
        )
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = response.json()
            portfolio_df = pd.DataFrame(columns=["name", "weight"])
            for etf in response_dict["etf_positions"]:
                portfolio_df.loc[etf["etf"]["asset"]["ticker"], "name"] = etf[
                    "etf"
                ]["asset"]["name"]
                portfolio_df.loc[etf["etf"]["asset"]["ticker"], "weight"] = etf[
                    "weight"
                ]
            return portfolio_df
        else:
            print(
                f"Failed to fetch data for fund ID {fund_id}. Status code: {response.status_code}"
            )
            return None


investments_client = InvestmentsClient()
