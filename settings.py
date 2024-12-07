from pydantic import SecretStr
from pydantic_settings import BaseSettings
from typing import TypeVar

Self = TypeVar("Self", bound="__BaseSettings")


class __BaseSettings(BaseSettings):
    @classmethod
    def load_from_env_vars(cls) -> Self:
        return cls()


class AlphaVantageClientSettings(__BaseSettings):
    alphavantage_api_key: SecretStr


class InvestmentsAPISettings(__BaseSettings):
    investments_api_url: SecretStr
