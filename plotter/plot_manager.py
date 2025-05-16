from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from enums.indicator import Indicator
from utils.logger import get_logger

pio.templates.default = "plotly_dark"


class PlotManager:
    def __init__(self, df: pd.DataFrame, indicators: Optional[List[Indicator]] = None):
        self.df = df
        self.indicators = indicators
        self.logger = get_logger(__name__)
        self.positions: List[Dict[str, Any]] = []

    def add_position_marker(self, fig: go.Figure, entry_time, exit_time, entry_price, exit_price, tp_price, sl_price):
        color_tp = "rgba(0, 255, 0, 0.2)"  # Verde claro
        color_sl = "rgba(255, 0, 0, 0.2)"  # Rojo claro

        # Rectángulo hasta TP
        fig.add_shape(
            type="rect",
            x0=entry_time,
            x1=exit_time,
            y0=entry_price,
            y1=tp_price,
            fillcolor=color_tp,
            opacity=0.8,
            line_width=0,
            layer="below"
        )

        # Rectángulo hasta SL
        fig.add_shape(
            type="rect",
            x0=entry_time, x1=exit_time,
            y0=entry_price,
            y1=sl_price,
            fillcolor=color_sl,
            opacity=0.8,
            line_width=0,
            layer="below"
        )

    def add_trade_markers(self, fig, trades):
        start_time = self.df['time'].iloc[0]
        for i, trade in enumerate(trades):
            if trade['open_time'] < start_time:
                continue

            entry_time = trade["open_time"]
            entry = trade["entry"]
            direction = trade["type"].value
            texthover = f'{i} {direction}\n Entry:{entry:.2f}\n SL:{trade["sl"]}\n TP:{trade["tp"]}'
            fig.add_trace(go.Scatter(
                x=[entry_time],
                y=[entry],
                mode='markers',
                marker={
                    "symbol": "circle",
                    "size": 5,
                    "color": "gray",
                    "line": {"width": 1, "color": "black"}
                },
                name=f'{direction} Entry',
                hovertext=texthover,
                showlegend=False
            ))

            # Línea hacia salida si existe
            if "exit_price" in trade and "exit_time" in trade:
                exit_price = trade["exit_price"]
                fig.add_trace(go.Scatter(
                    x=[entry_time, trade["exit_time"]],
                    y=[entry, exit_price],
                    mode="lines",
                    line={"dash": "dot", "color": "gray"},
                    name=f"{i} Trade Path",
                    showlegend=False
                ))

                fig.add_trace(go.Scatter(
                    x=[trade["exit_time"]],
                    y=[exit_price],
                    mode='markers',
                    marker={
                        "symbol": "circle",
                        "size": 5,
                        "color": "gray",
                        "line": {"width": 1, "color": "black"}
                    },
                    name=f'{direction} Exit',
                    hovertext=f'{i} {direction} Reason: {trade["exit_reason"]} Profit: {trade["profit"]:.2f}',
                    showlegend=False
                ))
                self.add_position_marker(
                    fig,
                    entry_time,
                    trade["exit_time"],
                    entry,
                    exit_price,
                    trade["tp"],
                    trade["sl"]
                )

    def set_positions(self, positions: List[Dict[str, Any]]):
        self.positions = positions

    def plot(
        self,
        title: str = "Asset Chart",
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ):
        """ Generates the chart of candles + indicators.

        Args:
            title (str, optional): The title of the chart. Defaults to "Asset Chart".
            start_idx (int, optional): The index of the first candle to show. Defaults to 0.
            end_idx (Optional[int], optional): The index of the last candle to show. Defaults to None.
        """

        df = self.df.copy()
        if end_idx is None:
            end_idx = len(df)

        df = df.iloc[start_idx:end_idx]
        self.df = df
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.7, 0.3],
            subplot_titles=(title, "Super TDI")
        )
        
        fig.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Candle'
        ))
        
        self.add_indicators(fig, df)
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=1000,
            plot_bgcolor="black",
            paper_bgcolor="black",
            font={"color": "white", "size": 12},
        )
        if self.positions:
            self.add_trade_markers(fig, self.positions)
       
        fig.show()

    def add_indicators(self, fig, df):
        if self.indicators is None:
            return
        
        mapped_indicators = {
            Indicator.BOLL: self.add_bollinger,
            Indicator.SMMA: self.add_smma,
            Indicator.TREND_SIGNALS: self.add_trend_signals,
            Indicator.RSI: self.add_rsi
        }
          
        for indicator in self.indicators:
            if indicator not in mapped_indicators:
                self.logger.warning(f"Indicator {indicator} not found in mapped_indicators")
                continue

            mapped_indicators[indicator](fig, df)

    def add_rsi(self, fig, df):
        if 'rsi' not in df.columns:
            return
        
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['rsi'],
            name='RSI',
            line={"color": "yellow", "dash": "dot"}
        ), row=2, col=1)
        
        for level, color in [(25, 'lime'), (35, 'yellow'), (50, 'white'), (65, 'yellow'), (75, 'red')]:
            fig.add_hline(y=level, line={"dash": "dot", "color": color}, row=2, col=1)

        fig.update_yaxes(title_text="", row=2, col=1)

    def add_tdi_subplot(self, fig, df):
        rsi_period = 10
        band_length = 20
        bull_ma_length = 1
        bear_ma_length = 5
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        rs = avg_gain / avg_loss
        key_rsi_l = 'rsi_1'
        df[key_rsi_l] = 100 - (100 / (1 + rs))

        df['ma'] = df[key_rsi_l].rolling(window=band_length).mean()
        df['stdev'] = df[key_rsi_l].rolling(window=band_length).std()
        df['up_band'] = df['ma'] + 2 * df['stdev']
        df['dn_band'] = df['ma'] - 2 * df['stdev']
        df['mid_band'] = (df['up_band'] + df['dn_band']) / 2
        df['bulls_ma'] = df[key_rsi_l].rolling(window=bull_ma_length).mean()
        df['bears_ma'] = df[key_rsi_l].rolling(window=bear_ma_length).mean()

    def add_bollinger(self, fig, df):
        if 'upper' in df.columns and 'lower' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['upper'],
                name="Bollinger Upper (OverBought)",
                line={"color": "red", "width": 1}
            ))

            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['lower'],
                name="Bollinger Lower (OverSold)",
                line={"color": "green", "width": 1}
            ))

    def add_smma(self, fig, df):
        if 'smma' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['smma'],
                line={"color": "orange", "width": 1},
                name='TrendLine (SMMA)'
            ))

    def add_trend_signals(self, fig, df):
        if 'buy_signal' in df.columns and 'sell_signal' in df.columns:
            buy_signals = df[df['buy_signal'].notna()]
            sell_signals = df[df['sell_signal'].notna()]
            fig.add_trace(go.Scatter(
                x=buy_signals['time'],
                y=buy_signals['buy_signal'],
                mode='markers',
                marker={"symbol": "triangle-up", "color": "green", "size": 15},
                name='Buy Signal'
            ))
            fig.add_trace(go.Scatter(
                x=sell_signals['time'],
                y=sell_signals['sell_signal'],
                mode='markers',
                marker={"symbol": "triangle-down", "color": "red", "size": 15},
                name='Sell Signal'
            ))


if __name__ == "__main__":
    df = pd.read_csv("history/XAUUSD.sml_M15_history.csv")
    plot_manager = PlotManager(df)
    plot_manager.plot()
