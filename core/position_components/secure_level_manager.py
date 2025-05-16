from typing import Any, Dict
from utils.logger import get_logger


class SecureLevelManager:
    def __init__(self, trigger_pips: float, secure_pips: float):
        self.trigger_pips = trigger_pips
        self.secure_pips = secure_pips
        self.active = False
        self.logger = get_logger(__name__)

    def should_apply(self, current_profit_pips: float) -> bool:
        is_apply = not self.active and current_profit_pips > self.trigger_pips
        if is_apply:
            self.logger.info(f"Secure level applied at {current_profit_pips} pips")
        return is_apply

    def apply(self, position: Dict[str, Any], current_profit_pips: float, current_price: float):
        if position['type'].value == 'BUY':
            if current_profit_pips >= self.secure_pips:
                position['sl'] = current_price - (self.secure_pips / 10)
            else:
                position['sl'] = position['entry']
        else:
            if position['entry'] - current_price > self.secure_pips:
                position['sl'] = current_price + self.secure_pips
            else:
                position['sl'] = position['entry']
        self.active = True
