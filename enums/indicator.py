from enum import Enum


class Indicator(Enum):
    BOLL = "BOLL"
    SMMA = "SMMA"
    TREND_SIGNALS = "TREND_SIGNALS"
    RSI = "RSI"


indicator_keys = {
    Indicator.BOLL: ["ma", "upper", "lower"],
    Indicator.SMMA: ["smma"],
    Indicator.TREND_SIGNALS: ["trend", "up", "dn", "buy_signal", "sell_signal"],
    Indicator.RSI: ["rsi"]
}
