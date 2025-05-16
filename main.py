import pandas as pd

from core.backtest_from_closed_trades import BacktestFromClosedTrades

if __name__ == "__main__":
    df = pd.read_csv("export/backtest_15m_positions_1745850561.csv", parse_dates=['entry_time', 'exit_time'])
    backtester = BacktestFromClosedTrades(df)
    portfolio = backtester.run_backtest()
    print(backtester.get_stats(portfolio))
    backtester.plot(portfolio)
