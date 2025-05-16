from typing import Any, Dict, List

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import BALANCE


def plot_complete_performance_dashboard(df, summary):
    if "pnl" not in df.columns:
        print("La columna 'pnl' no está en el DataFrame.")
        return

    pnl = df["pnl"].cumsum()
    rolling_max = pnl.cummax()
    drawdown = rolling_max - pnl

    # PnL + Drawdown Graph
    rows_scoreboard = (len(summary) + 2) // 3
    fig = make_subplots(
        rows=rows_scoreboard + 1,
        cols=3,
        row_heights=[0.15] * rows_scoreboard + [0.55],
        specs=[[{"type": "indicator"}] * 3] * rows_scoreboard + [[{"colspan": 3, "type": "xy"}, None, None]],
        vertical_spacing=0.03
    )

    # Scoreboard
    labels = list(summary.keys())
    values = [f"{v:.2f}" if isinstance(v, float) else str(v) for v in summary.values()]

    for i, (label, value) in enumerate(zip(labels, values)):
        row = i // 3 + 1
        col = i % 3 + 1
        fig.add_trace(go.Indicator(
            mode="number",
            value=float(value.replace('%', '')) if '%' in value else float(value),
            number={'suffix': '%' if '%' in value else ''},
            title={"text": label},
            domain={'row': row - 1, 'column': col - 1}
        ), row=row, col=col)

    # PnL y Drawdown
    fig.add_trace(go.Scatter(
        y=pnl,
        mode='lines+markers',
        name='PnL acumulado',
        line={"color": "green"}
    ), row=rows_scoreboard + 1, col=1)

    fig.add_trace(go.Scatter(
        y=drawdown,
        mode='lines',
        name='Drawdown absoluto',
        line={"color": "red", "dash": "dot"}
    ), row=rows_scoreboard + 1, col=1)

    fig.update_layout(
        title='📊 Trading Performance Dashboard',
        template='plotly_dark',
        height=220 * rows_scoreboard + 400,
        showlegend=True
    )

    fig.show()


def calculate_max_drawdown_percent_from_closed_positions(closed_positions: List[Dict[str, Any]]) -> float:
    if not closed_positions:
        return 0.0

    balances = [pos["balance"] for pos in closed_positions]

    peak = balances[0]
    max_drawdown_pct = 0.0

    for balance in balances:
        if balance > peak:
            peak = balance
        drawdown_pct = (peak - balance) / peak * 100
        if drawdown_pct > max_drawdown_pct:
            max_drawdown_pct = drawdown_pct

    return max_drawdown_pct


def calculate_max_drawdown_from_closed_positions(closed_positions: List[Dict[str, Any]]) -> float:
    if not closed_positions:
        return 0.0

    balances = [pos["balance"] for pos in closed_positions]

    peak = balances[0]
    max_drawdown = 0.0

    for balance in balances:
        if balance > peak:
            peak = balance
        drawdown = peak - balance
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def plot_performance_dashboard(closed_positions: List[Dict[str, Any]], summary: Dict[str, Any]):
    if not closed_positions:
        print("No closed positions to show.")
        return

    trades_data = []
    for pos in closed_positions:
        entry = pos["entry"]
        exit_price = pos["exit_price"]
        ttype = pos["type"]
        direction = 1 if ttype == "buy" else -1
        pnl = (exit_price - entry) * direction

        trades_data.append({
            "time_entry": pos["open_time"],
            "time_exit": pos["exit_time"],
            "entry_price": entry,
            "exit_price": exit_price,
            "pnl": pnl,
            "type": ttype,
            "zone": pos.get("zone", "N/A"),
            "reason": pos.get("exit_reason", "N/A"),
        })

    times = [pos["open_time"] for pos in closed_positions]
    balances = [pos["balance"] for pos in closed_positions]
    rolling_max = np.maximum.accumulate(balances)
    drawdowns = rolling_max - balances
    drawdowns_pct = (drawdowns / rolling_max) * 100

    max_drawdown_percent = max(drawdowns_pct)
    max_drawdown = max(drawdowns)
    summary["max_drawdown_percent"] = max_drawdown_percent
    summary["max_drawdown"] = max_drawdown
    # Scoreboard layout
    rows_scoreboard = (len(summary) + 2) // 3
    fig = make_subplots(
        rows=rows_scoreboard + 1,
        cols=3,
        row_heights=[0.15] * rows_scoreboard + [0.55],
        specs=[[{"type": "indicator"}] * 3] * rows_scoreboard + [[{"colspan": 3, "type": "xy"}, None, None]],
        vertical_spacing=0.03
    )

    labels = list(summary.keys())
    values = [f"{v:.2f}" if isinstance(v, float) else str(v) for v in summary.values()]

    for i, (label, value) in enumerate(zip(labels, values)):
        row = i // 3 + 1
        col = i % 3 + 1
        fig.add_trace(go.Indicator(
            mode="number",
            value=float(value.replace('%', '')) if '%' in value else float(value),
            number={'suffix': '%' if '%' in value else ''},
            title={"text": label},
            domain={'row': row - 1, 'column': col - 1}
        ), row=row, col=col)

    fig.add_trace(go.Scatter(
        x=times,
        y=balances,
        name='Balance',
        line={"color": "blue"}
    ), row=rows_scoreboard + 1, col=1)
    
    fig.add_trace(go.Scatter(
        x=times,
        y=[BALANCE] * len(times),
        name='',
        line={"color": "gray", "dash": "dot"}
    ), row=rows_scoreboard + 1, col=1)

    fig.update_layout(
        title='📊 Trading Performance Dashboard',
        template='plotly_dark',
        height=220 * rows_scoreboard + 400,
        showlegend=True
    )
    fig.show()
