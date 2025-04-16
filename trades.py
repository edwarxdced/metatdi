import pandas as pd
import numpy as np


def resumen_trades(trades_df: pd.DataFrame, balance_inicial: float = 10000.0):
    trades_df['profit'] = trades_df['result']
    trades_df['balance'] = trades_df['profit'].cumsum() + balance_inicial

    total_ganado = trades_df[trades_df['profit'] > 0]['profit'].sum()
    total_perdido = trades_df[trades_df['profit'] < 0]['profit'].sum()
    total_neto = trades_df['profit'].sum()
    winrate = (trades_df['profit'] > 0).mean() * 100

    resumen = {
        'Balance Inicial': round(balance_inicial, 2),
        'Ganancia Total': round(total_ganado, 2),
        'Pérdida Total': round(total_perdido, 2),
        'Ganancia Neta': round(total_neto, 2),
        'Balance Final': round(balance_inicial + total_neto, 2),
        'Winrate (%)': round(winrate, 2),
        'Total Trades': len(trades_df)
    }

    return resumen, trades_df

def simulate_trades(df: pd.DataFrame, rrr: float = 1.0, lookback: int = 5) -> pd.DataFrame:
    trades: list[dict] = []
    position: tuple[str, float, float, float, pd.Timestamp] | None = None

    for i in range(len(df)):
        row = df.iloc[i]

        if position is None:
            if not np.isnan(row['buy_signal']):
                entry_price = row['close']
                sl = df['low'].iloc[max(i - lookback, 0):i].min()
                tp = entry_price + (entry_price - sl) * rrr
                position = ('long', entry_price, sl, tp, row['time'])
            elif not np.isnan(row['sell_signal']):
                entry_price = row['close']
                sl = df['high'].iloc[max(i - lookback, 0):i].max()
                tp = entry_price - (sl - entry_price) * rrr
                position = ('short', entry_price, sl, tp, row['time'])

        elif position:
            pos_type, entry, sl, tp, entry_time = position
            hit_tp = row['high'] >= tp if pos_type == 'long' else row['low'] <= tp
            hit_sl = row['low'] <= sl if pos_type == 'long' else row['high'] >= sl

            if hit_tp or hit_sl:
                exit_price = tp if hit_tp else sl
                result = {
                    'type': pos_type,
                    'entry_time': entry_time,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'exit_time': row['time'],
                    'exit': exit_price,
                    'result': round(exit_price - entry, 2) if pos_type == 'long' else round(entry - exit_price, 2)
                }
                trades.append(result)
                position = None 

    return pd.DataFrame(trades)
