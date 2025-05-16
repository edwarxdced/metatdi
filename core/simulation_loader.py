from typing import Optional

import pandas as pd


class SimulationLoader:
    def __init__(self, ticks_path: str, historical_path: Optional[str] = None):
        """
        ticks_path: Path to the csv file with format time, tick
        historical_path: (optional) Path to the csv file with historical candles (for indicators or starting point)
        """
        self.ticks_path = ticks_path
        self.historical_path = historical_path
        self.ticks_df = None
        self.historical_df = None

    def load_data(self):
        """Loads the data from the csv files."""
        self.ticks_df = pd.read_csv(self.ticks_path, parse_dates=["time"])
        if self.historical_path:
            self.historical_df = pd.read_csv(self.historical_path, parse_dates=["time"])

    def filter_by_start_date(self, start_date: pd.Timestamp):
        """Filters the DataFrames to start the simulation from a specific date."""
        if self.ticks_df is not None:
            self.ticks_df = self.ticks_df[self.ticks_df["time"] >= start_date].reset_index(drop=True)
        
        if self.historical_df is not None:
            self.historical_df = self.historical_df[self.historical_df["time"] <= start_date].reset_index(drop=True)

    def get_ticks(self):
        """Returns ticks as arrays ready to simulate."""
        
        if self.ticks_df is None:
            raise ValueError("Ticks DataFrame is not loaded")
        times = self.ticks_df["time"].to_list()
        prices = self.ticks_df["tick"].values
        return times, prices

    def get_historical(self):
        """Returns the historical DataFrame (optional, if loaded)."""
        return self.historical_df
