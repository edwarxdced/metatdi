from typing import List, Optional

import numpy as np
from numba import njit

from config import RSI_PERIOD


@njit
def rsi_numba(closes: np.ndarray, period: int) -> np.ndarray:
    rsi = np.empty(len(closes))
    rsi[:] = np.nan

    if len(closes) < period + 1:
        return rsi

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.empty(len(deltas))
    avg_loss = np.empty(len(deltas))
    avg_gain[:] = np.nan
    avg_loss[:] = np.nan

    # Inicialización primer promedio
    avg_gain[period - 1] = np.mean(gains[:period])
    avg_loss[period - 1] = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

    rs = avg_gain / avg_loss
    rsi_values = 100.0 - (100.0 / (1.0 + rs))

    rsi[period:] = rsi_values[period - 1:]

    return rsi


class RSIIncremental:
    def __init__(self, period: int = RSI_PERIOD):
        self.period = period
        self.last_avg_gain = None
        self.last_avg_loss = None
        self.prev_close = None
        self.ready = False
        self.current_rsi = None

    def initialize(self, closes: np.ndarray):
        if len(closes) < 2:
            return

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])

        self.last_avg_gain = avg_gain
        self.last_avg_loss = avg_loss

        rs = avg_gain / avg_loss
        self.current_rsi = 100 - (100 / (1 + rs))

        self.prev_close = closes[-1]
        self.ready = True

    def update(self, current_close: float) -> float:
        if not self.ready or self.prev_close is None:
            return np.nan

        delta = current_close - self.prev_close
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0

        self.last_avg_gain = (self.last_avg_gain * (self.period - 1) + gain) / self.period
        self.last_avg_loss = (self.last_avg_loss * (self.period - 1) + loss) / self.period

        rs = self.last_avg_gain / self.last_avg_loss if self.last_avg_loss != 0 else 0
        self.current_rsi = 100 - (100 / (1 + rs)) if rs != 0 else 100

        self.prev_close = current_close

        return self.current_rsi


class RSIFastRolling:
    def __init__(self, period: int):
        self.period = period
        self.gains: List[float] = []
        self.losses: List[float] = []
        self.prev_close: Optional[float] = None
        self.ready: bool = False
        self.current_rsi: float = np.nan

    def initialize(self, closes: np.ndarray):
        if len(closes) < self.period:
            return

        deltas = np.diff(closes)
        for delta in deltas[-self.period:]:
            gain = max(delta, 0)
            loss = max(-delta, 0)
            self.gains.append(gain)
            self.losses.append(loss)

        if len(self.gains) >= self.period:
            self.ready = True
            self.current_rsi = self.calculate_rsi()

        self.prev_close = closes[-1]

    def update(self, current_close: float) -> float:
        if self.prev_close is None:
            self.prev_close = current_close
            return np.nan

        delta = current_close - self.prev_close
        gain = max(delta, 0)
        loss = max(-delta, 0)

        self.gains.append(gain)
        self.losses.append(loss)

        if len(self.gains) > self.period:
            self.gains.pop(0)
        if len(self.losses) > self.period:
            self.losses.pop(0)

        self.prev_close = current_close

        if len(self.gains) < self.period:
            self.ready = False
            return np.nan

        self.ready = True
        self.current_rsi = self.calculate_rsi()
        return self.current_rsi

    def calculate_rsi(self) -> float:
        avg_gain = np.mean(self.gains) if self.gains else 0.0
        avg_loss = np.mean(self.losses) if self.losses else 0.0

        if avg_loss == 0:
            return 100.0
        if avg_gain == 0:
            return 0.0

        rs = avg_gain / avg_loss
        return float(100.0 - (100.0 / (1.0 + rs)))
