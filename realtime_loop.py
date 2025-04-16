import time
import pandas as pd
from config import EMAIL_ACCOUNT, API_PASSWORD, API_KEY
from capital.login import login
from capital.historical_candles import get_historical_candles
from capital.epics import Epics
from capital.ws_client import start_websocket
from tick_handler import RealTimeHandler
from datetime import datetime
df = pd.DataFrame()

start_market = 2

def run_realtime_bot():
    global df, last_candle_time

    print("⏳ Iniciando bot con WebSocket...")
    headers, cst, x_token, ws_url = login(EMAIL_ACCOUNT, API_PASSWORD, API_KEY)

    _, df = get_historical_candles(headers, epic=Epics.GOLD, limit=500)
    handler = RealTimeHandler(df)

    start_websocket(cst, x_token, epic=Epics.GOLD, on_message_callback=handler.handle_tick_ws_client, ws_url=ws_url)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    run_realtime_bot()