"""
Reglas de confirmación de señales para el sistema de trading Super TDI + Bollinger.

BUY Setup:
- RSI por debajo de 50 o rebotando en zona 35 / 25
- Cruce alcista: bulls_ma (verde) cruza por encima de bears_ma (rojo)
- El precio toca o rompe la banda inferior de Bollinger y luego se mete de nuevo dentro

SELL Setup:
- RSI por encima de 50 o rebotando en zona 65 / 75
- Cruce bajista: bulls_ma cruza por debajo de bears_ma
- El precio toca o rompe la banda superior y luego vuelve dentro

Estas reglas están diseñadas para confirmar señales reales con intención y evitar entradas débiles.
"""

from crossed import crossed_above, crossed_below


def confirm_tdi_buy(row):
    return row["rsi"] < 50 and row["bulls_ma"] > row["bears_ma"]

def confirm_tdi_sell(row):
    return row["rsi"] > 50 and row["bears_ma"] > row["bulls_ma"]

def confirm_bollinger_rejection(prev, current, direction):
    if direction == "BUY":
        return prev["close"] < prev["lower"] and current["close"] > current["lower"]
    elif direction == "SELL":
        return prev["close"] > prev["upper"] and current["close"] < current["upper"]
    return False

def is_valid_buy(prev, current)->bool:
    return (
        current["rsi"] < 50 and
        prev["bulls_ma"] <= prev["bears_ma"] and current["bulls_ma"] > current["bears_ma"] and
        prev["close"] < prev["lower"] and current["close"] > current["lower"]
    )

def is_valid_sell(prev, current)->bool:
    return (
        current["rsi"] > 50 and
        prev["bulls_ma"] >= prev["bears_ma"] and current["bulls_ma"] < current["bears_ma"] and
        prev["close"] > prev["upper"] and current["close"] < current["upper"]
    )