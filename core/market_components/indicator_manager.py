from typing import List, Optional, Tuple

import numpy as np

from config import (ATR_PERIOD, BOLLINGER_PERIOD, DESVIATION, MULTIPLIER,
                    RSI_PERIOD, SMMA_LENGTH)
from enums.indicator import Indicator
from indicators_tools.atr import true_range, update_ema
from indicators_tools.bollinger import bollinger_numba
from indicators_tools.rsi import RSIFastRolling
from indicators_tools.smma import smma_numba
from indicators_tools.trend_signals import update_trend_signal
from models.candle import Candle
from utils.logger import get_logger


class IndicatorManager:
    def __init__(self, auto_save: bool = True, indicators: Optional[List[Indicator]] = None):
        self.logger = get_logger(__name__)
        self.auto_save: bool = auto_save
        self.indicators: Optional[List[Indicator]] = indicators
        self.ma: List[float] = [np.nan] * BOLLINGER_PERIOD
        self.upper: List[float] = [np.nan] * BOLLINGER_PERIOD
        self.lower: List[float] = [np.nan] * BOLLINGER_PERIOD
        self.smma: List[float] = [np.nan] * BOLLINGER_PERIOD
        self.trend: List[int] = []
        self.up: List[float] = []
        self.dn: List[float] = []

        self.prev_atr: Optional[float] = None
        self.current_atr: Optional[float] = None
        self.prev_up: float = 0.0
        self.prev_dn: float = 0.0
        self.trend_val: int = -1

        self.rsi: List[float] = [np.nan] * BOLLINGER_PERIOD
        self.rsi_calculator: Optional[RSIFastRolling] = None

    def initialize_rsi(self, closes: np.ndarray):
        if self.rsi_calculator is None:
            self.rsi_calculator = RSIFastRolling(period=RSI_PERIOD)
        
        if not self.rsi_calculator.ready:
            self.rsi_calculator.initialize(closes)
    
    def update_indicators(self, closes: List[float]) -> bool:
        if self.indicators is None:
            return False

        if len(self.indicators) == 0:
            return False

        closes_array = np.array(closes[-BOLLINGER_PERIOD:])
        if len(closes_array) < BOLLINGER_PERIOD:
            return False
        
        ma = None
        upper = None
        lower = None
        latest_smma = None
        
        if self.indicators is None:
            return False
        
        if Indicator.BOLL in self.indicators:
            ma, upper, lower = self.__bollinger_bands(closes_array)
            if ma is not None and upper is not None and lower is not None and self.auto_save:
                self.ma.append(ma)
                self.upper.append(upper)
                self.lower.append(lower)
       
        if Indicator.SMMA in self.indicators:
            latest_smma = self.__smma(closes_array)
            if latest_smma is not None and self.auto_save:
                self.smma.append(latest_smma)

        if Indicator.RSI in self.indicators:
            if self.rsi_calculator is None:
                self.initialize_rsi(closes_array)

            if self.rsi_calculator is not None and self.rsi_calculator.ready:
                current_rsi = self.rsi_calculator.update(closes_array[-1])
                self.rsi.append(current_rsi)

        return True

    def __bollinger_bands(self, closes_array: np.ndarray) -> Tuple[float | None, float | None, float | None]:
        ma, upper, lower = bollinger_numba(
            closes=closes_array,
            period=BOLLINGER_PERIOD,
            std_multiplier=DESVIATION
        )
        
        if np.isnan(ma):
            return None, None, None
        
        return ma, upper, lower
        
    def __smma(self, closes_array: np.ndarray) -> float | None:
        smma_result = smma_numba(closes_array, length=SMMA_LENGTH)
        latest_smma = smma_result[-1]
        if np.isnan(latest_smma):
            return None
        
        return latest_smma
    
    def calculate_trend_signals(
        self,
        current_candle: Candle,
        prev_close: float
    ) -> Tuple[int | None, float | None, float | None]:
        if prev_close is None:
            return None, None, None

        tr = true_range(current_candle.high, current_candle.low, prev_close)

        if self.prev_atr is None:
            current_atr = tr
        else:
            current_atr = update_ema(self.prev_atr, tr, ATR_PERIOD)

        self.current_atr = current_atr
        self.prev_atr = current_atr

        trend_val, up, dn = update_trend_signal(
            close=current_candle.close,
            high=current_candle.high,
            low=current_candle.low,
            prev_close=prev_close,
            prev_up=self.prev_up,
            prev_dn=self.prev_dn,
            trend_val=self.trend_val,
            atr=current_atr,
            multiplier=MULTIPLIER
        )

        self.prev_up = up
        self.prev_dn = dn
        self.trend_val = trend_val

        if self.auto_save:
            self.trend.append(trend_val)
            self.up.append(up)
            self.dn.append(dn)

        return trend_val, up, dn
