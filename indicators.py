import pandas as pd
import numpy as np
from config import BOLLINGER_PERIOD, DESVIATION, MULTIPLIER, ATR_PERIOD, USE_ATR



def calculate_bollinger(df: pd.DataFrame, period: int = BOLLINGER_PERIOD, std_multiplier: float = DESVIATION):
    df['ma'] = df['close'].rolling(window=period).mean()
    df['std'] = df['close'].rolling(window=period).std()
    df['upper'] = df['ma'] + std_multiplier * df['std']
    df['lower'] = df['ma'] - std_multiplier * df['std']
    return df

def smma(series: pd.Series, length: int) -> pd.Series:
    smma_values = np.zeros(len(series))
    smma_values[0] = series.ewm(span=length, adjust=False).mean().iloc[0]  # EMA inicial

    for i in range(1, len(series)):
        smma_values[i] = (smma_values[i-1] * (length - 1) + series.iloc[i]) / length

    return pd.Series(smma_values, index=series.index)


def simulate_trend_signals(df: pd.DataFrame, multiplier: float = MULTIPLIER, atr_period: int = ATR_PERIOD, use_atr: bool = USE_ATR):
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


def calculate_super_tdi(df: pd.DataFrame) -> pd.DataFrame:
    rsi_period = 10
    band_length = 20
    bull_ma_length = 1
    bear_ma_length = 5

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    df['ma'] = df['rsi'].rolling(window=band_length).mean()
    df['stdev'] = df['rsi'].rolling(window=band_length).std()
    df['up_band'] = df['ma'] + 2 * df['stdev']
    df['dn_band'] = df['ma'] - 2 * df['stdev']
    df['mid_band'] = (df['up_band'] + df['dn_band']) / 2

    df['bulls_ma'] = df['rsi'].rolling(window=bull_ma_length).mean()
    df['bears_ma'] = df['rsi'].rolling(window=bear_ma_length).mean()

    return df