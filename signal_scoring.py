# Crear archivo signal_scoring.py con la lógica para analizar señales y generar resumen

import pandas as pd

def classify_rsi_zone(rsi):
    if pd.isna(rsi): return "N/A"
    if rsi <= 25: return "Hard Buy"
    elif rsi <= 35: return "Soft Buy"
    elif rsi >= 75: return "Hard Sell"
    elif rsi >= 65: return "Soft Sell"
    else: return "Neutral"

def detect_tdi_crossover(df):
    df["tdi_crossover"] = (
        (df["bulls_ma"] > df["bears_ma"]) & (df["bulls_ma"].shift(1) <= df["bears_ma"].shift(1)) |
        (df["bulls_ma"] < df["bears_ma"]) & (df["bulls_ma"].shift(1) >= df["bears_ma"].shift(1))
    )
    return df

def detect_bollinger_rejection(df):
    df["bollinger_rejection"] = (
        ((df["trend"] == 1) & (df["close"] > df["lower"])) |
        ((df["trend"] == -1) & (df["close"] < df["upper"]))
    )
    return df

def score_signal(row):
    score = 0
    if row["rsi_zone"] in ["Hard Buy", "Soft Buy", "Hard Sell", "Soft Sell"]:
        score += 1
    if row.get("tdi_crossover", False):
        score += 1
    if row.get("bollinger_rejection", False):
        score += 1
    return score

def analyze_signals(df):
    df["rsi_zone"] = df["rsi"].apply(classify_rsi_zone)
    df = detect_tdi_crossover(df)
    df = detect_bollinger_rejection(df)
    df["score"] = df.apply(score_signal, axis=1)
    return df[["time", "close", "trend", "score", "tdi_crossover", "bollinger_rejection", "rsi_zone"]]


if __name__ == "__main__":
    df = pd.read_csv("history/gold_minute_15_simulated_signals.csv")
    df = analyze_signals(df)
    print(df)

