import numpy as np
from numba import njit

from config import SMMA_LENGTH


@njit
def smma_numba(series: np.ndarray, length: int = SMMA_LENGTH) -> np.ndarray:
    """
    Calcula SMMA (Smoothed Moving Average) usando Numba para máxima velocidad.

    Args:
        series (np.ndarray): Array de precios (floats).
        length (int): Periodo para suavizado.

    Returns:
        np.ndarray: Array con los valores SMMA.
    """
    n = len(series)
    if n == 0:
        return np.empty(0)

    smma_values = np.empty(n)
    smma_values[0] = series[0]

    inv_length = 1.0 / length  # Precalcular división

    for i in range(1, n):
        smma_values[i] = (smma_values[i - 1] * (length - 1) + series[i]) * inv_length

    return smma_values
