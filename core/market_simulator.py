from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd

from config import LOT_SIZE, RSI_PERIOD
from core.market_components.candle_manager import CandleManager
from core.market_components.indicator_manager import IndicatorManager
from core.market_components.signal_manager import SignalManager
from core.position_manager import PositionManager
from enums.indicator import Indicator, indicator_keys
from enums.type_signals import TypeSignal
from utils.logger import get_logger
from utils.trades_utils import calculate_initial_tp_sl


class MarketSimulator:

    def __init__(self, timeframe: int = 15, indicators: Optional[List[Indicator]] = None):
        self.logger = get_logger(__name__)
        self.candle_manager = CandleManager(timeframe)
        self.indicator_manager = IndicatorManager(indicators=indicators)
        self.signal_manager = SignalManager()
        self.position_manager = PositionManager()
        self.candle_time: Optional[datetime] = None
        self.indicators: Optional[List[Indicator]] = indicators

    def is_candle_closed(self, candle_time: datetime) -> bool:
        return self.candle_manager.next_open_time is not None and candle_time >= self.candle_manager.next_open_time

    def process_tick(self, price: float, candle_time: datetime):
        if candle_time >= datetime(2025, 4, 25, 6, 15) and candle_time <= datetime(2025, 4, 25, 7, 5):
            self.logger.info(f"Time {candle_time} Price {price}")
        
        if self.position_manager.active_position:
            self.position_manager.update_position(price=price, time=candle_time)

        self.candle_time = candle_time
        self.candle_manager.build_candle(price, candle_time)
        
        if self.is_candle_closed(candle_time):
            self.finalize_current_candle()

    def finalize_current_candle(self):
        if self.candle_manager.current_candle is None:
            return
    
        current_closes = self.candle_manager.closes.copy()
        if len(current_closes) > RSI_PERIOD:
            current_closes.pop(0)
            current_closes.append(self.candle_manager.current_candle.close)
        
        is_success = self.indicator_manager.update_indicators(
            current_closes,
        )
        if is_success and len(self.indicator_manager.ma) > 0:
            self.candle_manager.current_candle.ma = self.indicator_manager.ma[-1]
            self.candle_manager.current_candle.upper = self.indicator_manager.upper[-1]
            self.candle_manager.current_candle.lower = self.indicator_manager.lower[-1]
            self.candle_manager.current_candle.smma = self.indicator_manager.smma[-1]
        
        if self.candle_manager.prev_close is None or self.candle_manager.current_candle is None:
            return

        prev_trend = self.indicator_manager.trend_val
        trend_val, up, dn = self.indicator_manager.calculate_trend_signals(
            self.candle_manager.current_candle,
            self.candle_manager.prev_close
        )

        current_close = self.candle_manager.current_candle.close
        buy, sell = self.signal_manager.detect_signal(
            prev_trend,
            trend_val,
            current_close
        )

        self.candle_manager.current_candle.trend = trend_val
        self.candle_manager.current_candle.up = up
        self.candle_manager.current_candle.dn = dn
        self.candle_manager.current_candle.buy_signal = buy
        self.candle_manager.current_candle.sell_signal = sell
        self.candle_manager.save_candle()

        self.try_open_position()
        self.candle_manager.current_candle = None

    def check_open_position(self):
        if self.position_manager.active_position is None:
            return
        
        current_position = self.position_manager.active_position
        candle = self.candle_manager.current_candle
        current_price = candle.close
        buy_signal = candle.buy_signal
        sell_signal = candle.sell_signal
        force_close_position = self.position_manager.force_close_position

        if current_position["type"] == TypeSignal.BUY and sell_signal is not None and not np.isnan(sell_signal):
            force_close_position(
                current_price,
                self.candle_manager.current_candle.time,
                "CHANGE_TREND_TO_SELL"
            )

        elif current_position["type"] == TypeSignal.SELL and buy_signal is not None and not np.isnan(buy_signal):
            force_close_position(
                current_price,
                self.candle_manager.current_candle.time,
                "CHANGE_TREND_TO_BUY"
            )

    def try_open_position(self):
        if self.position_manager.active_position is not None:
            self.check_open_position()
            return

        buy_signal = self.candle_manager.current_candle.buy_signal
        sell_signal = self.candle_manager.current_candle.sell_signal

        if buy_signal is not None and not np.isnan(buy_signal):
            lows = self.candle_manager.lows.copy()
            highs = self.candle_manager.highs.copy()
            if len(highs) > 2:
                highs.pop(-1)
            
            if len(lows) > 2:
                lows.pop(-1)

            tp, sl = calculate_initial_tp_sl(
                lows=lows,
                highs=highs,
                entry=buy_signal,
                direction=TypeSignal.BUY,
                rsi=self.indicator_manager.rsi[-1]
            )
            self.position_manager.open_position(
                trade_type=TypeSignal.BUY,
                entry_price=buy_signal,
                tp=tp,
                sl=sl,
                lot_size=LOT_SIZE,
                time=self.candle_time,
            )
        elif sell_signal is not None and not np.isnan(sell_signal):
            lows = self.candle_manager.lows.copy()
            highs = self.candle_manager.highs.copy()
            if len(highs) > 2:
                highs.pop(-1)
            
            if len(lows) > 2:
                lows.pop(-1)
            tp, sl = calculate_initial_tp_sl(
                lows=lows,
                highs=highs,
                entry=sell_signal,
                direction=TypeSignal.SELL,
                rsi=self.indicator_manager.rsi[-1]
            )
            self.position_manager.open_position(
                trade_type=TypeSignal.SELL,
                entry_price=sell_signal,
                lot_size=LOT_SIZE,
                tp=tp,
                sl=sl,
                time=self.candle_manager.current_candle.time,
            )

    def export_to_dataframe(self) -> pd.DataFrame:
        payload = {
            "time": self.candle_manager.times,
            "open": self.candle_manager.opens,
            "high": self.candle_manager.highs,
            "low": self.candle_manager.lows,
            "close": self.candle_manager.closes
        }

        if self.indicators is None:
            return pd.DataFrame(payload)

        for indicator in self.indicators:
            try:
                for key in indicator_keys.get(indicator, []):
                    if key in ["buy_signal", "sell_signal"]:
                        payload[key] = getattr(self.signal_manager, key)
                        continue
                    
                    payload[key] = getattr(self.indicator_manager, key)
            except Exception as e:
                self.logger.error(f"Error exporting indicator {indicator} to dataframe: {e}", exc_info=True)
        
        return pd.DataFrame(payload)
