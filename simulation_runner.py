import pandas as pd
from tick_handler import RealTimeHandler
from plot_candles import plot_candles
from datetime import datetime, timezone

class TradingSimulator:
    def __init__(self, historical_df_15m: pd.DataFrame, simulation_df_1m: pd.DataFrame):
        self.bot = RealTimeHandler(historical_df_15m)
        self.simulation_df = simulation_df_1m

    def run(self):
        print(f"🔁 Iniciando simulación con {len(self.simulation_df)} ticks...")
        for _, row in self.simulation_df.iterrows():
            price = row["close"]
            candle_time = row["time"]
            for price in [row["open"], row["low"], row["high"], row["close"]]:
                self.bot.process_tick(price, candle_time)
            
            if candle_time >= datetime(2025, 4, 2, 23, 45, tzinfo=timezone.utc):
                plot_candles(self.bot.df, title="XAUUSD M15 Simulated")
                self.bot.signals.to_csv("history/gold_minute_15_simulated_signals.csv", index=False)
                breakpoint()
        
        print("✅ Simulación finalizada.")


if __name__ == "__main__":
    historical_df_15m = pd.read_csv("history/gold_minute_15.csv")
    simulation_df_1m = pd.read_csv("history/gold_minute.csv")
    
    
    historical_df_15m["time"] = pd.to_datetime(historical_df_15m["time"])
    simulation_df_1m["time"] = pd.to_datetime(simulation_df_1m["time"])
    
    start_date = pd.Timestamp(2025, 3, 31, 23, 45,  tz="UTC")
    historical_df_15m = historical_df_15m[historical_df_15m["time"] <= start_date]
    simulation_df_1m = simulation_df_1m[simulation_df_1m["time"] >= start_date]
    simulator = TradingSimulator(historical_df_15m, simulation_df_1m)
    try:
        simulator.run()
    except KeyboardInterrupt:
        simulator.bot.df.to_csv("history/gold_minute_15_simulated.csv", index=False)
        plot_candles(simulator.bot.df, title="XAUUSD M15 Simulated")
        

