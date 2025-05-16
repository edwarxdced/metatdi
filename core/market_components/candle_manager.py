from datetime import datetime
from typing import List, Optional

import numpy as np

from models.candle import Candle
from utils.calculate_next_open_time import get_next_open_time
from utils.logger import get_logger


class CandleManager:
    def __init__(self, timeframe: int):
        self.timeframe = timeframe
        self.logger = get_logger(__name__)
        self.times: List[datetime] = []
        self.opens: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        self.closes: List[float] = []

        self.current_candle: Optional[Candle] = None
        self.next_open_time: Optional[datetime] = None
        self.candle_time: Optional[datetime] = None
        self.prev_close: Optional[float] = None

    def create_new_candle(self, price: float, candle_time: datetime) -> Candle:
        if self.current_candle is None:
            self.prev_close = price
        else:
            self.prev_close = self.current_candle.close

        self.current_candle = Candle(
            time=candle_time,
            open=price,
            high=price,
            low=price,
            close=price,
            ma=None,
            upper=None,
            lower=None,
            smma=None,
            trend=None,
            up=None,
            dn=None,
            buy_signal=np.nan,
            sell_signal=np.nan,
        )
        self.next_open_time = get_next_open_time(candle_time, self.timeframe)
        return self.current_candle

    def build_candle(self, price: float, candle_time: datetime) -> Candle:
        if self.current_candle is None:
            self.current_candle = self.create_new_candle(price, candle_time)

        self.prev_close = self.current_candle.close
        self.current_candle.close = price

        if price > self.current_candle.high:
            self.current_candle.high = price
        if price < self.current_candle.low:
            self.current_candle.low = price

        return self.current_candle

    def save_candle(self):
        if self.current_candle is None:
            self.logger.error("Current candle is None")
            return
        
        self.times.append(self.current_candle.time)
        self.opens.append(self.current_candle.open)
        self.highs.append(self.current_candle.high)
        self.lows.append(self.current_candle.low)
        self.closes.append(self.current_candle.close)

        self.prev_close = self.current_candle.close
