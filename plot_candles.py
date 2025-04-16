import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import json
from trades import resumen_trades
from indicators import calculate_super_tdi, calculate_bollinger, smma, simulate_trend_signals
from config import  LENGTH
from plotly.subplots import make_subplots
from datetime import timezone


pio.templates.default = "plotly_dark"





def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df['buy_signal'] = np.where((df['trend'] == 1) & (df['trend'].shift(1) == -1), df['low'], np.nan)
    df['sell_signal'] = np.where((df['trend'] == -1) & (df['trend'].shift(1) == 1), df['high'], np.nan)
    return df

def add_bollinger(fig, df):
    fig.add_trace(go.Scatter(x=df['time'], y=df['upper'], name="OverBought", line=dict(color='RED')))
    fig.add_trace(go.Scatter(x=df['time'], y=df['lower'], name="OverSold", line=dict(color='GREEN')))
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['trendline'],
        line=dict(color='orange', width=1),
        name='TrendLine (SMMA)'
    ))
    
def add_tdi_subplot(fig, df):
    fig.add_trace(go.Scatter(x=df['time'], y=df['up_band'], name='Upper Band', line=dict(color='green', dash='dot')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['dn_band'], name='Lower Band', line=dict(color='red', dash='dot')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['mid_band'], name='Mid Band', line=dict(color='gray', dash='dash')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['bulls_ma'], name='Bulls (Green)', line=dict(color='lime')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['bears_ma'], name='Bears (Red)', line=dict(color='darkred')), row=2, col=1)

    # Zonas
    for level, color in [(25, 'lime'), (35, 'yellow'), (50, 'white'), (65, 'yellow'), (75, 'red')]:
        fig.add_hline(y=level, line=dict(dash='dot', color=color), row=2, col=1)

    fig.update_yaxes(title_text="TDI", row=2, col=1)


def mark_tdi_zones(fig, df):
    for i in range(len(df)):
        rsi = df['rsi'].iloc[i]
        green = df['bulls_ma'].iloc[i]
        red = df['bears_ma'].iloc[i]
        x = df['time'].iloc[i]

        if pd.isna(rsi) or pd.isna(green) or pd.isna(red):
            continue

        # Zona de compra
        if green > red:
            if rsi <= 25:
                fig.add_trace(go.Scatter(x=[x], y=[rsi],
                                         mode='markers', marker=dict(color='lime', size=6),
                                         name="Hard Buy Zone"), row=2, col=1)
            elif rsi <= 35:
                fig.add_trace(go.Scatter(x=[x], y=[rsi],
                                         mode='markers', marker=dict(color='yellow', size=6),
                                         name="Soft Buy Zone"), row=2, col=1)

        # Zona de venta
        elif green < red:
            if rsi >= 75:
                fig.add_trace(go.Scatter(x=[x], y=[rsi],
                                         mode='markers', marker=dict(color='red', size=6),
                                         name="Hard Sell Zone"), row=2, col=1)
            elif rsi >= 65:
                fig.add_trace(go.Scatter(x=[x], y=[rsi],
                                         mode='markers', marker=dict(color='orange', size=6),
                                         name="Soft Sell Zone"), row=2, col=1)

def load_data_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"])
    return df

def load_data_json(json_path: str) -> pd.DataFrame:
    with open(json_path, 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    df.drop(columns=['timestamp'], inplace=True)
    df = df.sort_values(by='time').reset_index(drop=True)
    return df

def plot_candles(df: pd.DataFrame, title: str = "XAUUSD M15"):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "Super TDI")
    )
    # Velas
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Precio'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['buy_signal'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'
    ))
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['sell_signal'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'
    ))
    add_tdi_subplot(fig, df)
    mark_tdi_zones(fig, df)
    
    fig.update_layout(
        title=title,
        xaxis_title='Tiempo',
        yaxis_title='Precio',
        xaxis_rangeslider_visible=False,
        height=1000,
        template="plotly_dark",
        plot_bgcolor="black",
        paper_bgcolor="black",
        font=dict(color="white", size=12),
        
    )
    add_bollinger(fig, df)
    fig.show()



if __name__ == "__main__":
    df = load_data_csv("history/gold_minute_15.csv")

    df = calculate_bollinger(df)
    df['trendline'] = smma(df['close'], length=LENGTH)
    df = simulate_trend_signals(df)
    df = generate_signals(df)
    df = calculate_super_tdi(df)

    plot_candles(df)
    #trades_df = simulate_trades(df, rrr=1.0, lookback=5)
    #resumen, trades_df = resumen_trades(trades_df, balance_inicial=10000)
    # Mostrar resumen
    #for k, v in resumen.items():
    #    print(f"{k}: {v}")
    
    breakpoint()
    
