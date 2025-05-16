from typing import Tuple

import numpy as np
import pandas as pd
from numba import njit

from config import BOLLINGER_PERIOD, DESVIATION


def bollinger(df: pd.DataFrame, period: int = BOLLINGER_PERIOD, std_multiplier: float = DESVIATION):
    df['ma'] = df['close'].rolling(window=period).mean()
    df['std'] = df['close'].rolling(window=period).std()
    df['upper'] = df['ma'] + std_multiplier * df['std']
    df['lower'] = df['ma'] - std_multiplier * df['std']
    return df


def bollinger_numpy(closes: np.ndarray, period: int = BOLLINGER_PERIOD, std_multiplier: float = DESVIATION):
    """
    Calcula Bollinger Bands usando arrays de NumPy.

    Parameters:
        closes (np.ndarray): Array de precios de cierre.
        period (int): Número de periodos para calcular la media y desviación.
        std_multiplier (float): Multiplicador para calcular las bandas.

    Returns:
        Tuple (ma, upper, lower) correspondientes al último valor calculado.
    """
    if len(closes) < period:
        return None, None, None

    closes_window = closes[-period:]

    ma = closes_window.mean()
    std = closes_window.std()

    upper = ma + std_multiplier * std
    lower = ma - std_multiplier * std

    return ma, upper, lower


@njit
def bollinger_numba(
    closes: np.ndarray,
    period: int = BOLLINGER_PERIOD,
    std_multiplier: float = DESVIATION
) -> Tuple[float, float, float]:
    """
    Calcula Bollinger Bands usando Numba para máxima velocidad.

    Parameters:
        closes (np.ndarray): Array de precios de cierre.
        period (int): Número de periodos para calcular la media y desviación.
        std_multiplier (float): Multiplicador para calcular las bandas.

    Returns:
        Tuple (ma, upper, lower) correspondientes al último valor calculado.
    """
    if closes.shape[0] < period:
        return np.nan, np.nan, np.nan

    # Selecciona la ventana de cierre reciente
    closes_window = closes[-period:]

    mean = 0.0
    for i in range(closes_window.shape[0]):
        mean += closes_window[i]
    mean /= closes_window.shape[0]

    variance = 0.0
    for i in range(closes_window.shape[0]):
        diff = closes_window[i] - mean
        variance += diff * diff
    variance /= closes_window.shape[0]

    std = np.sqrt(variance)

    upper = mean + std_multiplier * std
    lower = mean - std_multiplier * std

    return mean, upper, lower
