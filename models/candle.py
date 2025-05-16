from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    ma: Optional[float] = None
    upper: Optional[float] = None
    lower: Optional[float] = None
    smma: Optional[float] = None
    trend: Optional[int] = None
    up: Optional[float] = None
    dn: Optional[float] = None
    buy_signal: Optional[float] = None
    sell_signal: Optional[float] = None
