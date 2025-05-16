from typing import Optional
import numpy as np
import pandas as pd
import vectorbt as vbt


def align_to_candle_time(ts: pd.Timestamp, timeframe: int = 15) -> pd.Timestamp:
    return ts.floor(f'{timeframe}min')


def align_timestamp(ts: pd.Timestamp, timeframe_min: int = 15) -> pd.Timestamp:
    """
    Alinea cualquier timestamp al inicio de su vela correspondiente.
    """
    return ts.floor(f'{timeframe_min}min')


def find_candle_index(candle_times: pd.Series, target_time: pd.Timestamp) -> Optional[int]:
    """
    Busca el indice de la vela que corresponde al timestamp objetivo.
    """
    target_time = align_timestamp(pd.to_datetime(target_time))
    candle_times = pd.to_datetime(candle_times).dt.floor('15min')

    mask = candle_times == target_time
    if mask.any():
        return mask.idxmax()
    else:
        return None


def process_trade_entry_exit(trade_row, candles_df):
    """
    Alinea y encuentra los indices de entry y exit para un trade.
    """
    entry_time_aligned = align_timestamp(trade_row['entry_time'])
    exit_time_aligned = align_timestamp(trade_row['exit_time'])

    entry_idx = find_candle_index(candles_df['time'], entry_time_aligned)
    exit_idx = find_candle_index(candles_df['time'], exit_time_aligned)

    return entry_idx, exit_idx


class BacktestFromClosedTrades:
    def __init__(self, trades_df: pd.DataFrame):
        self.trades_df = trades_df.copy()

    def prepare_orders(self):
        direction_map = {'BUY': 1, 'SELL': -1}
        self.trades_df['direction'] = self.trades_df['type'].map(direction_map)
        self.trades_df['size'] = self.trades_df['lot_size'] * self.trades_df['direction']
        self.trades_df['entry_time'] = pd.to_datetime(self.trades_df['entry_time'])
        self.trades_df['exit_time'] = pd.to_datetime(self.trades_df['exit_time'])

    def run_backtest(self, initial_balance=10000, fees=0.0001, slippage=0.0):
        self.prepare_orders()

        data = pd.read_csv("export/backtest_15m_results_1745850560.csv")
        data['time'] = pd.to_datetime(data['time'])
        self.trades_df['entry_candle_time'] = self.trades_df['entry_time'].apply(align_to_candle_time)
        self.trades_df['exit_candle_time'] = self.trades_df['exit_time'].apply(align_to_candle_time)

        entries = np.zeros(len(data), dtype=bool)
        exits = np.zeros(len(data), dtype=bool)
        sizes = np.zeros(len(data))
                
        # Para cada trade, marca en qué vela entra y sale
        for _, trade in self.trades_df.iterrows():
            entry_idx, exit_idx = process_trade_entry_exit(trade, data)
            if entry_idx is not None and exit_idx is not None:
                direction = 1 if trade['type'] == 'BUY' else -1
                entries[entry_idx] = True
                exits[exit_idx] = True
                sizes[entry_idx] = trade['lot_size'] * direction

        pf = vbt.Portfolio.from_signals(
            open=data['open'].values,
            high=data['high'].values,
            low=data['low'].values,
            close=data['close'].values,
            entries=entries,
            exits=exits,
            size=sizes,
            init_cash=10000,    # tu balance inicial
            fees=0.0001,        # ejemplo: 0.01%
            slippage=0.0        # sin slippage
        )

        return pf

    def get_stats(self, portfolio):
        return portfolio.stats()

    def plot(self, portfolio):
        fig = portfolio.plot()
        fig.update_layout(
            width=1800,
            height=1000,
        )
        fig.show()


# Ejemplo de uso:
# df = pd.read_csv("path_to_your_trades.csv", parse_dates=['entry_time', 'exit_time'])
# backtester = BacktestFromClosedTrades(df)
# portfolio = backtester.run_backtest()
# print(backtester.get_stats(portfolio))
# backtester.plot(portfolio)
