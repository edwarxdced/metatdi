from datetime import datetime

from enums.type_signals import TypeSignal
from utils.trades_utils import get_trade_parameters


def format_trade_message(direction: TypeSignal, last_row, df):
    entry = last_row['close']
    rsi = last_row['rsi']
    tp, sl, rrr, zone = get_trade_parameters(
        direction=direction,
        rsi=rsi,
        entry=entry,
        stop_distance=2,
        df=df
    )
    icon = "🟢" if direction.value == TypeSignal.BUY.value else "🔴"

    msg = f"""
🚨 New Signal Anticipated


{icon} {direction.value}
🎯 Entry Price: {entry:.2f}
💰 TP: {tp:.2f}
🛡️ SL: {sl:.2f}


📊 TDI Zone: {zone}
🔢 RRR: {rrr}:1
🕒 Time: {last_row['time']}
"""
    return msg


def format_rejection_alert(signal_type, confirm_price, confirm_time, early_confirmation: bool = False):
    icon = "🟢" if signal_type == "BUY" else "🔴"
    early_confirmation_msg = "🚨 Early Confirmation" if early_confirmation else "🔢 Close candle confirmation"
    msg = f"""
❌ Signal Rejected

{icon} {signal_type} (No Confirmed)
⛔ Close without confirmation: {confirm_price:.2f}
🕒 Time: {confirm_time}


{early_confirmation_msg}
"""
    return msg


def format_confirmation_alert(signal_type, confirm_price, confirm_time, early_confirmation: bool = False):
    icon = "🟢" if signal_type == "BUY" else "🔴"
    early_confirmation_msg = "🚨 Early Confirmation" if early_confirmation else "🔢 Close candle confirmation"
    msg = f"""
✅  Signal Confirmed
                            
{icon} {signal_type} (Confirmed)
✅ Confirmed at: {confirm_price:.2f}
🕒 Time: {confirm_time}

{early_confirmation_msg}
"""
    return msg


def format_position_opened_message(trade_type: TypeSignal, entry_price: float, tp: float, sl: float, time: datetime):
    msg = f"""
🚀 Trade OPENED ({trade_type.value}) at {entry_price:.2f}

💰 TP: {tp:.2f}
🛡️ SL: {sl:.2f}
🕒 Time: {time}
"""
    return msg


def format_break_even_applied_message(trade_type: TypeSignal, entry_price: float, time: datetime) -> str:
    msg = f"""
🟡 Break-Even applied.
SL moved to entry ({entry_price:.2f})
🕒 Time: {time}
"""
    return msg


def format_trailing_stop_updated_message(trade_type: TypeSignal, current_price: float, time: datetime) -> str:
    msg = f"""
🔁 Trailing SL updated to {current_price:.2f}
🔢 Current Price: {current_price:.2f}
🕒 Time: {time}
"""
    return msg


def format_position_closed_message(
    trade_type: TypeSignal, price: float, time: datetime,
    reason: str, entry: float, lot_size: float
) -> str:
    icon = "💰" if reason == "TP" else "🛑"
    if trade_type.value == "BUY":
        profit = (price - entry) * lot_size
    else:  # SELL
        profit = (entry - price) * lot_size

    result = "Profit" if profit >= 0 else "Loss"
    msg = f"""
{icon} Trade CLOSED ({trade_type.value}) at {price:.2f}

💼 {result}: {profit:.2f} USD
📊 Entry: {entry:.2f} | Lot: {lot_size}
💰 Exit: {price:.2f}
🕒 Time: {time}
🔢 Reason: {reason}
"""
    return msg
