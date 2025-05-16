import numpy as np
import pandas as pd
from numba import njit

from config import ATR_PERIOD, MULTIPLIER, USE_ATR


def simulate_trend_signals(
    df: pd.DataFrame,
    multiplier: float = MULTIPLIER,
    atr_period: int = ATR_PERIOD,
    use_atr: bool = USE_ATR
):
    # True Range
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda row: max(row['high'] - row['low'],
                        abs(row['high'] - row['close']),
                        abs(row['low'] - row['close'])), axis=1)
    
    if use_atr:
        atr = df['tr'].ewm(span=atr_period, adjust=False).mean().values
    else:
        atr = df['tr'].rolling(window=atr_period).mean().values

    close = df['close'].values
    trend = []
    up_series = []
    dn_series = []
    buy_signal = []
    sell_signal = []

    # Inicialización
    up = close[0] - multiplier * atr[0]
    dn = close[0] + multiplier * atr[0]
    trend_val = 1

    for i in range(len(df)):
        if i == 0:
            trend.append(trend_val)
            up_series.append(up)
            dn_series.append(dn)
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)
            continue

        # Guardar valores anteriores
        up1 = up
        dn1 = dn

        # Calcular valores actuales
        up = close[i] - multiplier * atr[i]
        dn = close[i] + multiplier * atr[i]

        if close[i - 1] > up1:
            up = max(up, up1)
        if close[i - 1] < dn1:
            dn = min(dn, dn1)

        # Actualizar tendencia
        if trend_val == -1 and close[i] > dn1:
            trend_val = 1
        elif trend_val == 1 and close[i] < up1:
            trend_val = -1

        # Señales
        prev_trend = trend[-1]
        buy_signal.append(close[i] if trend_val == 1 and prev_trend == -1 else np.nan)
        sell_signal.append(close[i] if trend_val == -1 and prev_trend == 1 else np.nan)

        # Guardar valores
        trend.append(trend_val)
        up_series.append(up)
        dn_series.append(dn)

    df['trend'] = trend
    df['up'] = up_series
    df['dn'] = dn_series
    df['buy_signal'] = buy_signal
    df['sell_signal'] = sell_signal
    return df


@njit
def update_trend_signal_early(
    close: float,
    high: float,
    low: float,
    prev_close: float,
    prev_up: float,
    prev_dn: float,
    prev_trend_val: int,  # <-- tendencia anterior guardada
    trend_val: int,  # <-- tendencia actual
    atr: float,
    multiplier: float
):
    """
    Calcula el nuevo estado de tendencia basado en el último tick.
    """
    # Calcular nuevos up y dn
    up = close - multiplier * atr
    dn = close + multiplier * atr

    if prev_close > prev_up:
        up = max(up, prev_up)
    if prev_close < prev_dn:
        dn = min(dn, prev_dn)

    # Actualizar la tendencia viva
    if trend_val == -1 and close > prev_dn:
        trend_val = 1
    elif trend_val == 1 and close < prev_up:
        trend_val = -1

    # Señales basadas en cambio de tendencia
    buy_signal = np.nan
    sell_signal = np.nan
    if trend_val == 1 and prev_trend_val == -1:
        buy_signal = close
    elif trend_val == -1 and prev_trend_val == 1:
        sell_signal = close

    return trend_val, up, dn, buy_signal, sell_signal


@njit
def update_trend_signal(
    close: float,
    high: float,
    low: float,
    prev_close: float,
    prev_up: float,
    prev_dn: float,
    trend_val: int,
    atr: float,
    multiplier: float
):
    """
    Actualiza trend, up y dn basados en el último tick. NO genera señales aquí.
    """
    up = close - multiplier * atr
    dn = close + multiplier * atr

    if prev_close > prev_up:
        up = max(up, prev_up)
    if prev_close < prev_dn:
        dn = min(dn, prev_dn)

    if trend_val == -1 and close > prev_dn:
        trend_val = 1
    elif trend_val == 1 and close < prev_up:
        trend_val = -1

    return trend_val, up, dn
