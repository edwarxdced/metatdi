
import traceback

import pandas as pd

from core.trade_replayer import TradeReplayer

if __name__ == "__main__":
    candles_df = pd.read_csv("history/gold_m15.csv")
    ticks_df = pd.read_csv("history/gold_minute_ticks.csv")
    trades_df = pd.read_csv("export/backtest_15m_positions_1745947487.csv")

    candles_df['time'] = pd.to_datetime(candles_df['time'])
    ticks_df['time'] = pd.to_datetime(ticks_df['time'])
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

    try:
        candles_df.drop(columns=['ma', 'volume'], inplace=True)
        replayer = TradeReplayer(candles_df, ticks_df, trades_df)
        replayer.filter_replay_range(trades_df['entry_time'][-4:])
        replayer.start_replay()
    except KeyboardInterrupt:
        exit(0)
    except Exception:
        traceback.print_exc()
        exit(1)
    finally:
        exit(0)
