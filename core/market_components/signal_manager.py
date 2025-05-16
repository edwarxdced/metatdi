from typing import List, Tuple

import numpy as np

from utils.logger import get_logger


class SignalManager:
    def __init__(self, auto_save: bool = True):
        self.auto_save: bool = auto_save
        self.buy_signal: List[float] = []
        self.sell_signal: List[float] = []
        self.logger = get_logger(__name__)

    def detect_signal(self, prev_trend: int, current_trend: int, close: float) -> Tuple[float, float]:
        val_buy = np.nan
        val_sell = np.nan
        
        if prev_trend == -1 and current_trend == 1:
            val_buy = close
        elif prev_trend == 1 and current_trend == -1:
            val_sell = close

        if self.auto_save:
            self.buy_signal.append(val_buy)
            self.sell_signal.append(val_sell)

        return val_buy, val_sell
     
