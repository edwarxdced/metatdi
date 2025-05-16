
from typing import List, Optional

import pandas as pd
from lightweight_charts import Chart

from enums.indicator import Indicator
from utils.logger import get_logger


class LightweightPlotter:
    def __init__(self, df: pd.DataFrame, indicators: Optional[List[Indicator]] = None):
        self.df = df
        self.indicators = indicators
        self.logger = get_logger(__name__)

    def __add_bollinger(self, chart: Chart):
        line_upper_params = {
            'color': 'red',
            'name': 'Bollinger Upper (OverBought)',
            'width': 1,
            'price_line': False,
        }
        line_upper = chart.create_line(**line_upper_params)
        upper_data = pd.DataFrame({
            'time': self.df['time'],
            'Bollinger Upper (OverBought)': self.df['upper']
        }).dropna()
        line_upper.set(upper_data)

        line_lower_params = {
            'color': 'green',
            'name': 'Bollinger Lower (OverSold)',
            'width': 1,
            'price_line': False,
        }
        line_lower = chart.create_line(**line_lower_params)
        lower_data = pd.DataFrame({
            'time': self.df['time'],
            'Bollinger Lower (OverSold)': self.df['lower']
        }).dropna()
        line_lower.set(lower_data)

    def __add_smma(self, chart: Chart):
        line_smma_params = {
            'color': 'orange',
            'name': 'SMMA',
            'width': 1,
            'price_line': False,
        }
        line_smma = chart.create_line(**line_smma_params)
        smma_data = pd.DataFrame({
            'time': self.df['time'],
            'SMMA': self.df['smma']
        }).dropna()
        line_smma.set(smma_data)

    def __add_trend_signals(self, chart: Chart):
        self.logger.info("Adding trend signals")
        buy_signal = self.df[self.df['buy_signal'].notna()]
        sell_signal = self.df[self.df['sell_signal'].notna()]
        for _, row in buy_signal.iterrows():
            chart.marker(time=row['time'], position='above', shape='arrow_up', color='green', text='Buy')
        for _, row in sell_signal.iterrows():
            chart.marker(time=row['time'], position='below', shape='arrow_down', color='red', text='Sell')

    def _add_indicators(self, chart: Chart):
        if self.indicators is None:
            return chart
        
        for indicator in self.indicators:
            if indicator == Indicator.BOLL:
                self.__add_bollinger(chart)
            elif indicator == Indicator.SMMA:
                self.__add_smma(chart)
            elif indicator == Indicator.TREND_SIGNALS:
                self.__add_trend_signals(chart)

    def plot(self):
        chart = Chart()
        chart.legend(visible=True)
        chart.set(self.df)
        self._add_indicators(chart)
        chart.show(block=True)
