import time
from typing import Any, List, Optional, Type

import pandas as pd

from core.simulation_loader import SimulationLoader
from core.simulation_runner import SimulationRunner
from enums.indicator import Indicator
from plotter.plot_manager import PlotManager
from utils.logger import get_logger
from utils.plot_perfomance import plot_performance_dashboard

TIMEFRAMES: List[int] = [15]
INDICATORS: List[Indicator] = [Indicator.TREND_SIGNALS, Indicator.BOLL, Indicator.SMMA, Indicator.RSI]
SUB_PLOTS: List[Any] = []
USE_LIGHTWEIGHT: bool = False
EXPORT_TO_CSV: bool = True
COMPARE_WITH_TREND_SIGNALS: bool = False
EXPORT_POSITION_CSV: bool = True

TICK_PATH: str = "history/gold_minute_ticks.csv"
HISTORICAL_PATH: str = "history/gold_m15.csv"
START_DATE: pd.Timestamp = pd.Timestamp(2025, 1, 1, 0, 0)
PLOTTER_TRADES: bool = True
PLOTTER_HISTORICAL: bool = True
PLOTTER_PERFORMANCE: bool = True
CLASS_USE_TO_PLOT: Type[PlotManager] = PlotManager


class Backtest:
    def __init__(self, loader: SimulationLoader, indicators: Optional[List[Indicator]] = None):
        self.logger = get_logger(__name__)
        self.loader = loader
        self.indicators = indicators
        self.timeframes = TIMEFRAMES
        self.sub_plots: List[Any] = []
        self.load_data()
    
    def load_data(self):
        self.loader.load_data()
        self.loader.filter_by_start_date(START_DATE)

    def run(self):
        for timeframe in TIMEFRAMES:
            self.run_backtest(timeframe, self.indicators)

    def run_backtest(self, timeframe: int, indicators: Optional[List[Indicator]] = None):
        runner = SimulationRunner(
            self.loader,
            timeframe=timeframe,
            indicators=indicators
        )
        runner.run(progress=False)
        df = runner.export_to_dataframe()
        
        if EXPORT_TO_CSV:
            self.logger.info("Exporting CSV...")
            filename = f"export/backtest_{timeframe}m_results_{int(time.time())}.csv"
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported to {filename}")

        if EXPORT_POSITION_CSV or PLOTTER_PERFORMANCE:
            self.logger.info("Exporting PositionS CSV...")
            filename = f"export/backtest_{timeframe}m_positions_{int(time.time())}.csv"
            positions_df = runner.bot.position_manager.export_closed_positions_to_dataframe()
            if EXPORT_POSITION_CSV:
                positions_df.to_csv(filename, index=False)
                self.logger.info(f"Exported to {filename}")
            
            if PLOTTER_PERFORMANCE:
                summary = runner.bot.position_manager.analyze_closed_positions()
                plot_performance_dashboard(runner.bot.position_manager.closed_positions, summary)
        
        if PLOTTER_HISTORICAL:
            self.logger.info("Plotting...")
            plotter = CLASS_USE_TO_PLOT(df[-500:], indicators)
            plotter.set_positions(runner.bot.position_manager.closed_positions[-500:])
            plotter.plot(start_idx=0, end_idx=500)
            self.logger.info("Plotted")


if __name__ == "__main__":
    backtest = Backtest(
        loader=SimulationLoader(TICK_PATH, HISTORICAL_PATH),
        indicators=INDICATORS
    )
    backtest.run()
