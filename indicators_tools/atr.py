import numpy as np
from numba import njit


@njit
def update_ema(prev_ema: float, value: float, period: int) -> float:
    alpha = 2 / (period + 1)
    return alpha * value + (1 - alpha) * prev_ema


@njit
def simple_moving_average(values: np.ndarray) -> float:
    return np.mean(values)


@njit
def true_range(high: float, low: float, close_prev: float) -> float:
    return max(
        high - low,
        abs(high - close_prev),
        abs(low - close_prev)
    )
