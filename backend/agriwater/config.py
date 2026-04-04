"""Configuration from environment."""

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class FarmSettings(BaseSettings):
    latitude: float = Field(default=12.37, alias="FARM_LATITUDE")
    longitude: float = Field(default=-1.52, alias="FARM_LONGITUDE")
    name: str = Field(default="Ferme Demo Ouagadougou", alias="FARM_NAME")


class TariffSettings(BaseSettings):
    """SONABEL tariff structure for Burkina Faso."""

    peak: float = Field(default=110.0, alias="TARIFF_PEAK")
    offpeak: float = Field(default=75.0, alias="TARIFF_OFFPEAK")
    peak_start: int = Field(default=7, alias="PEAK_HOURS_START")
    peak_end: int = Field(default=23, alias="PEAK_HOURS_END")
    subscribed_power_kw: float = Field(default=150.0, alias="SUBSCRIBED_POWER_KW")
    penalty_rate_fcfa: float = Field(default=200.0, alias="PENALTY_RATE_FCFA")


class Settings(BaseSettings):
    farm: FarmSettings = FarmSettings()
    tariff: TariffSettings = TariffSettings()


settings = Settings()
