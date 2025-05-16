import time
from datetime import datetime
from typing import List, Optional

import pandas as pd
from lightweight_charts import Chart # type: ignore

from core.position_manager import PositionManager
from core.position_components.break_even_manager import BreakEvenManager
from enums.type_signals import TypeSignal
from utils.logger import get_logger

BACK_CANDLES_START = 10
FRONT_CANDLES_END = 2


class TradeReplayer:
    def __init__(self, candles_df: pd.DataFrame, ticks_df: pd.DataFrame, trades_df: pd.DataFrame):
        self.candles_df = candles_df
        self.ticks_df = ticks_df
        self.trades_df = trades_df
        self.filtered_candles_df: Optional[pd.DataFrame] = None
        self.chart: Optional[Chart] = None
        self.play_speed: float = 0.05
        self.trades_appends: List[datetime] = []
        self.break_even_manager: Optional[BreakEvenManager] = None
        self.position_manager: PositionManager = PositionManager()
        self.logger = get_logger(__name__)

    def filter_replay_range(self, entry_times: List[datetime]):
        min_entry_time = min(entry_times)
        max_exit_time = self.trades_df[self.trades_df['entry_time'].isin(entry_times)]['exit_time'].max()

        mask = (self.candles_df['time'] >= min_entry_time) & (self.candles_df['time'] <= max_exit_time)
        selected_candles = self.candles_df.loc[mask]
        
        idx_first = selected_candles.index[0]
        idx_start = max(idx_first - BACK_CANDLES_START, 0)
        idx_end = max(idx_first - FRONT_CANDLES_END, 0)
        self.filtered_candles_df = self.candles_df.iloc[idx_start:idx_end + 1].reset_index(drop=True)
        if self.filtered_candles_df is None or self.filtered_candles_df.empty:
            raise ValueError("Not enough data to replay")
        
        start_date = self.filtered_candles_df['time'].iloc[- 1]
        self.filtered_ticks_df = self.ticks_df[self.ticks_df["time"] >= start_date].reset_index(drop=True)

    def start_replay(self):
        if self.filtered_candles_df is None:
            raise ValueError("Should call filter_replay_range() first")

        self.chart = Chart()
        self.chart.set(self.filtered_candles_df)
        self.chart.legend(visible=True)
        self.chart.show()
        self.filtered_ticks_df.rename(columns={'tick': 'price'}, inplace=True)
        
        detected_times = 0
        self.open_positions = False
        for _, row in self.filtered_ticks_df.iterrows():
            candle_time = row['time']
            price = row['price']
            self.chart.update_from_tick(row)

            trade = self.trades_df[self.trades_df['entry_time'] == row['time']]
            if not trade.empty:
                if detected_times >= 3:
                    self.add_markers(candle_time, trade)
                    self.trades_appends.append(candle_time)
                    time.sleep(self.play_speed)
                    detected_times = 0
                    continue
                else:
                    detected_times += 1
            
            if self.position_manager.active_position:
                closed = self.position_manager.update_position(price, candle_time)
                if closed:
                    self.add_marker_sell()
                    detected_times = 0
                
                time.sleep(self.play_speed)
            
            time.sleep(self.play_speed)

    def add_markers(self, current_time: datetime, trade):
        tp = trade['entry_tp'].iloc[0]
        sl = trade['entry_sl'].iloc[0]
        entry_price = trade['entry_price'].iloc[0]
        entry_time = trade['entry_time'].iloc[0]
        exit_time = trade['exit_time'].iloc[0]
        
        if self.chart is None:
            raise ValueError("Chart is not initialized")
        
        self.chart.marker(text=f'Buy ({entry_price})', shape='circle', position='inside', color='green')
        
        df_tp_line = pd.DataFrame({
            "time": [entry_time, exit_time],
            "TP": [tp, tp]
        })
        
        df_sl_line = pd.DataFrame({
            "time": [entry_time, exit_time],
            "SL": [sl, sl]
        })
        df_entry_line = pd.DataFrame({
            "time": [entry_time, exit_time],
            "Entry": [entry_price, entry_price]
        })

        tp_line = self.chart.create_line(name="TP", color='green', style='dotted', width=2)
        tp_line.set(df_tp_line)

        sl_line = self.chart.create_line(name="SL", color='red', style='dotted', width=2)
        sl_line.set(df_sl_line)

        entry_line = self.chart.create_line(name="Entry", color='gray', style='dotted', width=2)
        entry_line.set(df_entry_line)

        self.position_manager.open_position(TypeSignal.BUY, entry_price, tp, sl, lot_size=0.1, time=current_time)

    def add_marker_sell(self):
        last_closed = self.position_manager.closed_positions[-1]
        close_price = last_closed['exit_price']
        profit = last_closed['profit']
        if self.chart is None:
            raise ValueError("Chart is not initialized")
        self.chart.marker(text=f'Close ({close_price}) {profit:.2f}', shape='circle', position='inside', color='red')

    def add_break_even_line(self, trade):
        if self.chart is None:
            raise ValueError("Chart is not initialized")
        entry_price = trade['entry_price'].iloc[0]
        entry_time = trade['entry_time'].iloc[0]
        exit_time = trade['exit_time'].iloc[0]
        direction = 'BUY'
        for idx, level in enumerate(self.position_manager.break_even_manager.levels):
            if direction == 'BUY':
                activation_price = entry_price + (level.activate_pips / 10)
            else:  # SELL
                activation_price = entry_price - (level.activate_pips / 10)

            line_name = f"BE_Level_{idx + 1}"
            be_line = self.chart.create_line(name=line_name, color='yellow', style='dashed', width=1)
            be_line.set(pd.DataFrame({
                "time": [entry_time, exit_time],
                line_name: [activation_price, activation_price]
            }))
