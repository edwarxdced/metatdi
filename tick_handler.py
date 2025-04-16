import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
from config import BOLLINGER_PERIOD, DESVIATION, MULTIPLIER, ATR_PERIOD, USE_ATR, LENGTH
from indicators import calculate_bollinger, smma, simulate_trend_signals, calculate_super_tdi
from utils.telegram_alert import send_telegram_alert
from utils.message_formatter import format_trade_message
import json
from datetime import timezone
import traceback
from signal_tracker import SignalTracker
class RealTimeHandler:
    def __init__(self, historical_df: pd.DataFrame, timeframe: int = 15):
        self.df = historical_df.tail(500).copy().reset_index(drop=True)
        self.generate_indicators()
        self.last_signal_type = None
        self.signal_sent_in_candle = False
        self.trend_history = []
        self.trend_history_length = 4
        self.signal_tracker = SignalTracker()
        
        if self.df.empty:
            raise ValueError("No historical data provided")
        
        last_candle = self.df.iloc[-1]
        self.next_open_time = last_candle['time'] + timedelta(minutes=timeframe)
        self.signals = self.df[self.df[["buy_signal", "sell_signal"]].notna().any(axis=1)].copy()

        
        self.current_candle: Dict[str, Any] = {
            'time': last_candle['time'],
            'open': last_candle['open'],
            'high': last_candle['high'],
            'low': last_candle['low'],
            'close': last_candle['close'],
            'volume': last_candle['volume']
        }
        
        self.timeframe = timeframe
        print(f"Total current candle {len(self.df)}")
        
    def print_debug_info(self, timestamp: datetime, current_price: float):
        try:
            trend = 'BUY' if self.signals.iloc[-1]['trend'] == 1 else 'SELL'
            last_signal =  self.signals.iloc[-1]
            price_signal = 0
            if not last_signal.empty:
                price_signal = last_signal.buy_signal if trend == 'BUY' and last_signal.buy_signal is not None else last_signal.sell_signal

            print(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Price: {current_price}")
            print(f"Current trend: {trend} - Price signal: {price_signal} time: {last_signal.time}")
            
            if price_signal is not None:
                diff = current_price - price_signal if trend == 'BUY' else price_signal - current_price
                direction = "🔼" if diff > 0 else "🔽" if diff < 0 else "➖"
                pct_diff = diff / price_signal * 100
                print(f"Diferencia actual: {direction} {diff:.2f}")
                print(f"Variación desde la señal: {pct_diff:.2f}%")
            print("\n")
                
        except Exception as e:
            traceback.print_exc()
            print(f"Error printing debug info: {e}")

    
    def handle_tick_ws_client(self, ws, message: str):
        try:
            data = json.loads(message)
            if data.get('destination') == "ping":
                print("🫀 PING received")
                return
            
            payload = data.get('payload', {})
            if 'bid' not in payload:
                return
            
            price = payload['bid']
            timestamp = datetime.fromtimestamp(payload['timestamp'] / 1000)
            self.print_debug_info(timestamp, price)
            candle_time = timestamp.replace(minute=(timestamp.minute // 15) * 15, second=0, microsecond=0, tzinfo=timezone.utc)
            self.process_tick(price, candle_time)
        except Exception as e:
            print(f"Error processing tick: {e}")
            
    def handle_tick_http_client(self):
        ## TODO: Implement HTTP client
        pass
    
    
    def process_tick(self, price: float, candle_time: datetime):
        index_current_candle = self.df.index[-1]
            
        if candle_time >= self.next_open_time:
            print("Processing new candle")
            self.prorcess_new_candle(price, candle_time)
            self.df = pd.concat([self.df, pd.DataFrame([self.current_candle])], ignore_index=True)
            self.signal_sent_in_candle = False
        else:
            self.df.at[index_current_candle, 'close'] = price

            if price > self.df.iloc[-1]['high']:
                self.df.at[index_current_candle, 'high'] = price

            if price < self.df.iloc[-1]['low']:
                self.df.at[index_current_candle, 'low'] = price
        
        self.generate_indicators()
        self.check_anticipate_signal()
      
        self.df = self.df.tail(200).reset_index(drop=True)
        
        
    def generate_indicators(self):
        self.df = calculate_bollinger(self.df, period=BOLLINGER_PERIOD, std_multiplier=DESVIATION)
        self.df['trendline'] = smma(self.df['close'], length=LENGTH)
        self.df = simulate_trend_signals(self.df, multiplier=MULTIPLIER, atr_period=ATR_PERIOD, use_atr=USE_ATR)
        self.df = calculate_super_tdi(self.df)
        
    def prorcess_new_candle(self, price, candle_time):
        self.current_candle = {
            'time': candle_time,
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': 0
        }
        print(f"New candle with open: {price} at {candle_time}")
        self.next_open_time = candle_time + timedelta(minutes=self.timeframe)
        confirmed = self.signal_tracker.check_confirmation(self.current_candle)
        if confirmed is False:
            self.signals = self.signals.iloc[:-1]
        
        
    
    def check_anticipate_signal(self):
        if not self.current_candle or len(self.df) <= max(BOLLINGER_PERIOD, 20, LENGTH):
            return
        
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        self.trend_history.append(last["trend"])
        if len(self.trend_history) > self.trend_history_length:
            self.trend_history.pop(0)
            
        if all(t == last["trend"] for t in self.trend_history):

            if not self.signal_sent_in_candle:
                if last['trend'] == 1 and prev['trend'] == -1:
                    self.process_verify_signal(last, prev, "BUY")
                    self.signal_tracker.register_anticipate_signal(last, "BUY")
                elif last['trend'] == -1 and prev['trend'] == 1:
                    self.process_verify_signal(last, prev, "SELL")
                    self.signal_tracker.register_anticipate_signal(last, "SELL")
        else:
           pass
            
            
        
                    
    def process_verify_signal(self, last, prev, signal_type):
        if self.last_signal_type == signal_type:
            return
        
        msg = format_trade_message(signal_type, last, self.df)
        print(msg)
        self.signals = pd.concat([self.signals, pd.DataFrame([last])], ignore_index=True)
        self.signal_sent_in_candle = True
        self.last_signal_type = signal_type
        send_telegram_alert(msg)
