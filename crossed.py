import numpy as np
import pandas as pd

def crossed(series1, series2, direction=None):
    """
    Detecta si series1 cruzó a series2 en la última vela.
    direction: "above", "below", o None para ambos.
    Retorna una serie booleana.
    """
    if isinstance(series1, np.ndarray):
        series1 = pd.Series(series1)

    if isinstance(series2, (float, int, np.ndarray, np.integer, np.floating)):
        series2 = pd.Series(index=series1.index, data=series2)

    if direction is None or direction == "above":
        above = (series1 > series2) & (series1.shift(1) <= series2.shift(1))
    else:
        above = pd.Series([False] * len(series1), index=series1.index)

    if direction is None or direction == "below":
        below = (series1 < series2) & (series1.shift(1) >= series2.shift(1))
    else:
        below = pd.Series([False] * len(series1), index=series1.index)

    return (above | below).fillna(False) if direction is None else (above if direction == "above" else below).fillna(False)

def crossed_above(series1, series2):
    """Retorna True donde series1 cruza por encima de series2"""
    return crossed(series1, series2, "above")

def crossed_below(series1, series2):
    """Retorna True donde series1 cruza por debajo de series2"""
    return crossed(series1, series2, "below")