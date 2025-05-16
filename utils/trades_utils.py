from typing import List, Tuple

import numpy as np
import pandas as pd

from config import MIN_RRR, RRR_HARD, RRR_SOFT
from enums.type_signals import TypeSignal
from utils.logger import get_logger

logger = get_logger(__name__)


def get_trade_parameters(
    direction: TypeSignal, rsi: float, entry: float, df: pd.DataFrame,
    rrr_soft=RRR_SOFT, rrr_hard=RRR_HARD, min_rrr=MIN_RRR
) -> Tuple[float, float, float, str]:
    if direction.value == TypeSignal.BUY.value:
        if rsi <= 25:
            zone = "Hard Buy"
            rrr = rrr_hard
        elif rsi <= 35:
            zone = "Soft Buy"
            rrr = rrr_soft
        else:
            zone = "Neutral Buy"
            rrr = rrr_soft
    elif direction.value == TypeSignal.SELL.value:
        if rsi >= 75:
            zone = "Hard Sell"
            rrr = rrr_hard
        elif rsi >= 65:
            zone = "Soft Sell"
            rrr = rrr_soft
        else:
            zone = "Neutral Sell"
            rrr = rrr_soft
    else:
        zone = "N/A"
        rrr = rrr_soft

    # Calcula TP y SL
    # sl = entry - stop_distance if direction.value == TypeSignal.BUY.value else entry + stop_distance
    # tp = entry + stop_distance * rrr if direction.value == TypeSignal.BUY.value else entry - stop_distance * rrr

    lookback = 5
    max_lookback = 50
    if direction == TypeSignal.BUY:
        for i in range(1, max_lookback // lookback + 1):
            find_lookback = lookback * i
            recent_low = df.iloc[-find_lookback:]["low"].min()
            if recent_low < entry:
                break
        sl = recent_low
        tp = entry + abs(entry - sl) * max(rrr, min_rrr)
    
    else:
        recent_high = df.iloc[-lookback:]["high"].max()
        sl = recent_high
        tp = entry - abs(sl - entry) * max(rrr, min_rrr)
    
    return tp, sl, rrr, zone


def calculate_initial_tp_sl(
    lows: List[float],
    highs: List[float],
    entry: float,
    direction: TypeSignal,
    rsi: float,
    rrr_soft: float = RRR_SOFT,
    rrr_hard: float = RRR_HARD,
    min_rrr: float = MIN_RRR,
    lookback: int = 5,
    max_lookback: int = 50
):
    sl = None
    tp = None
    # Determinar zona y RRR basado en RSI
    if direction.value == TypeSignal.BUY.value:
        if rsi <= 25:
            rrr = rrr_hard
        elif rsi <= 35:
            rrr = rrr_soft
        else:
            rrr = rrr_soft
    elif direction.value == TypeSignal.SELL.value:
        if rsi >= 75:
            rrr = rrr_hard
        elif rsi >= 65:
            rrr = rrr_soft
        else:
            rrr = rrr_soft
    else:
        rrr = rrr_soft

    # Calcular SL y TP
    if direction == TypeSignal.BUY:
        # --- Buscar SL (últimos mínimos) ---
        for i in range(1, (max_lookback // lookback) + 1):
            find_lookback = lookback * i
            if len(lows) < find_lookback:
                break
            recent_low = np.min(lows[-find_lookback:])
            if recent_low < entry:
                sl = recent_low
                break
        if sl is None:
            sl = np.min(lows[-lookback:])

        # --- Buscar TP (últimos máximos) ---
        for i in range(1, (max_lookback // lookback) + 1):
            find_lookback = lookback * i
            if len(highs) < find_lookback:
                break
            
            recent_high = np.max(highs[-find_lookback:])
            if recent_high > entry:
                # if recent_high - entry < BREAK_EVEN_TRIGGER:
                #     tp = recent_high + BREAK_EVEN_TRIGGER
                # else:
                tp = recent_high
                break
        if tp is None:
            tp = entry + abs(entry - sl) * max(rrr, 1.0)
        risk = abs(entry - sl)
    else:  # SELL
        for i in range(1, (max_lookback // lookback) + 1):
            find_lookback = lookback * i
            if len(highs) < find_lookback:
                break
            recent_high = np.max(highs[-find_lookback:])
            if recent_high > entry:
                sl = recent_high
                break

        if sl is None:
            sl = np.max(highs[-lookback:])

        risk = abs(sl - entry)
        tp = entry - risk * max(rrr, min_rrr)

    return tp, sl
