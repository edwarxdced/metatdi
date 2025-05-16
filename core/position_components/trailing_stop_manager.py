from typing import Any, Dict, Optional

from utils.logger import get_logger


class TrailingStopManager:
    def __init__(self, start_pips: float, trailing_pips: float, step_pips: float):
        self.start_pips = start_pips
        self.trailing_pips = trailing_pips
        self.step_pips = step_pips
        self.last_trailing_price: Optional[float] = None
        self.logger = get_logger(__name__)

    def should_start(self, current_profit_pips: float) -> bool:
        return current_profit_pips >= self.start_pips

    def should_update(self, current_profit_pips: float) -> bool:
        if self.last_trailing_price is None:
            return True
        return abs(current_profit_pips - self.last_trailing_price) >= self.step_pips

    def apply(self, position: Dict[str, Any], current_price: float):
        if position['type'].value == 'BUY':
            new_sl = current_price - self.trailing_pips
            if new_sl > position['sl']:
                position['sl'] = new_sl
        else:
            position['sl'] = current_price + self.trailing_pips
        self.last_trailing_price = current_price
