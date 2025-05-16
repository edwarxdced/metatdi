import time
from datetime import datetime
from typing import List, Optional

from core.market_simulator import MarketSimulator
from core.simulation_loader import SimulationLoader
from enums.indicator import Indicator
from utils.logger import get_logger


class SimulationRunner:
    bot: Optional[MarketSimulator] = None
    
    def __init__(self, loader: SimulationLoader, timeframe: int = 15, indicators: Optional[List[Indicator]] = None):
        """
        loader: Instance of SimulationLoader already loaded
        timeframe: Timeframe in minutes for the simulation (e.g., 15m)
        """
        
        self.logger = get_logger(__name__)
        self.loader: SimulationLoader = loader
        self.bot: Optional[MarketSimulator] = None
        self.timeframe = timeframe
        self.indicators: Optional[List[Indicator]] = indicators
        self.times: list[datetime] = []
        self.prices: list[float] = []

        self._load_data()

    def _load_data(self):
        # Initialize times and prices from the loader
        self.times, self.prices = self.loader.get_ticks()
        self.bot = MarketSimulator(timeframe=self.timeframe, indicators=self.indicators)

    def run(self, progress: bool = False):
        total_ticks = len(self.times)
        self.logger.info(f"Running simulation with {total_ticks} ticks...")
        self.logger.info(f"Start time: {self.times[0]}")
        self.logger.info(f"End time: {self.times[-1]}")
        if self.bot is None:
            self.logger.error("Bot is not initialized")
            return

        time_start = time.time()
        for i in range(total_ticks):
            self.bot.process_tick(self.prices[i], self.times[i])
            if progress and i % 5000 == 0:
                self.logger.info(f"Processed {i}/{total_ticks} ticks...")
        
        self.bot.finalize_current_candle()
        time_end = time.time()
        self.logger.info(f"Simulation finished in {time_end - time_start} seconds.")

    def export_to_dataframe(self):
        if self.bot is None:
            raise ValueError("Bot is not initialized")
        return self.bot.export_to_dataframe()

    def reset(self):
        """Reset the simulation from zero."""
        self._load_data()
