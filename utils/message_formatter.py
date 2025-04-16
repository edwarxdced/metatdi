def format_trade_message(direction, last_row, df, lookback=5):
    entry = last_row['close']
    rsi = last_row['rsi']

    # Determinar zona
    if  "BUY" in direction:
        if rsi <= 25:
            zone = "Hard Buy"
            rrr = 2.0
        elif rsi <= 35:
            zone = "Soft Buy"
            rrr = 1.0
        else:
            zone = "Neutral Buy"
            rrr = 1.0
    elif "SELL" in direction:
        if rsi >= 75:
            zone = "Hard Sell"
            rrr = 2.0
        elif rsi >= 65:
            zone = "Soft Sell"
            rrr = 1.0
        else:
            zone = "Neutral Sell"
            rrr = 1.0
    else:
        zone = "N/A"
        rrr = 1.0

    # SL basado en swing previo
    icon = "🟢" if "BUY" in direction else "🔴"
    if "BUY" in direction:
        sl = df['low'].iloc[-lookback:].min()
        tp = entry + (entry - sl) * rrr
    else:
        sl = df['high'].iloc[-lookback:].max()
        tp = entry - (sl - entry) * rrr

    msg = f"""
🚨 New Signal Anticipated


{icon} {direction}
🎯 Entry Price: {entry:.2f}
💰 TP: {tp:.2f}
🛡️ SL: {sl:.2f}


📊 TDI Zone: {zone}
🔢 RRR: {rrr}:1
🕒 Time: {last_row['time']}
"""
    return msg


def format_rejection_alert(signal_type, confirm_price, confirm_time):
    icon = "🟢" if signal_type == "BUY" else "🔴"
    msg = f"""
❌ Signal Rejected
        
{icon} {signal_type} (No Confirmed)  
⛔ Close without confirmation: {confirm_price:.2f}  
🕒 Time: {confirm_time}
        """
    return msg


def format_confirmation_alert(signal_type, confirm_price, confirm_time):
    
    icon = "🟢" if signal_type == "BUY" else "🔴"
    msg = f"""
✅  Signal Confirmed
                            
{icon} {signal_type} (Confirmed)
✅ Confirmed at: {confirm_price:.2f}
🕒 Time: {confirm_time}
    """
    return msg



