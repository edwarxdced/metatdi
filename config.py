from dotenv import load_dotenv
import os

load_dotenv()
BOLLINGER_PERIOD = 34

DESVIATION = 1.75
MULTIPLIER = 0.9
ATR_PERIOD = 1
USE_ATR = True
LENGTH = 9
SMMA_LENGTH = 9
BREAK_EVEN_TRIGGER = 5
TRAILING_DISTANCE = 5
EARLY_CONFIRMATION_BODY_MULTIPLIER = 1.005
BALANCE = 10000
LOT_SIZE = 0.1
BREAK_EVENT_LEVELS = [
    [5, 10],
    [10, 20],
    [20, 35],
    [35, 50],
]


RRR_SOFT = 1.0
RRR_HARD = 2.0
MIN_RRR = 1.0
LOOKBACK = 5
RSI_PERIOD = 10
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WS_URL = "wss://api-streaming-capital.backend-capital.com/connect"
