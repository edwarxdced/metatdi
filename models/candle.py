from datetime import datetime

from pydantic import BaseModel


class Candle(BaseModel):
    """Model representing a trading candle with OHLCV data."""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
