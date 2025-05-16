from typing import Any, Dict, List, Optional

from utils.logger import get_logger


class BreakEvenLevel:
    def __init__(self, activate_pips: float, profit_pips: float):
        self.activate_pips = activate_pips
        self.profit_pips = profit_pips


class BreakEvenManager:
    def __init__(self, multi_level: bool = False):
        self.multi_level = multi_level
        self.levels: List[BreakEvenLevel] = []
        self.active_level_idx = 0
        self.logger = get_logger(__name__)
        # Solo para modo normal
        self.activate_pips: Optional[float] = None
        self.profit_pips: Optional[float] = None

    def set_normal(self, activate_pips: float, profit_pips: float = 0.0):
        self.multi_level = False
        self.activate_pips = activate_pips
        self.profit_pips = profit_pips

    def add_level(self, activate_pips: float, profit_pips: float):
        self.multi_level = True
        self.levels.append(BreakEvenLevel(activate_pips, profit_pips))

    def should_apply(self, current_profit_pips: float) -> bool:
        if self.multi_level:
            if self.active_level_idx >= len(self.levels):
                return False
            level = self.levels[self.active_level_idx]
            return current_profit_pips >= level.activate_pips
        else:
            if self.activate_pips is None:
                return False
            return current_profit_pips >= self.activate_pips

    def apply(self, position: Dict[str, Any], current_price: float):
        if self.multi_level:
            level = self.levels[self.active_level_idx]
            if position['type'].value == 'BUY':
                if self.active_level_idx == 0:
                    position['sl'] = position['entry']
                    position['tp'] = position['entry'] + (level.profit_pips / 10)
                    
                elif self.active_level_idx == 1:
                    if current_price >= position['entry'] + (level.activate_pips / 10):
                        position['sl'] = current_price
                    else:
                        position['sl'] = position['entry'] + (level.activate_pips / 10)
                    
                    position['tp'] = current_price + (level.profit_pips / 10)
                elif self.active_level_idx == 2:
                    position['sl'] = position['sl'] + (level.activate_pips / 10)
                    position['tp'] = current_price + (level.profit_pips / 10)
            else:
                position['sl'] = position['entry'] - (level.activate_pips / 10)
            
            self.logger.info(
                "Level: {} profit_pips: {} current_price: {} New SL: {} New TP: {}".format(
                    self.active_level_idx,
                    level.profit_pips,
                    current_price,
                    position['sl'],
                    position['tp']
                )
            )
            self.active_level_idx += 1
        else:
            if self.profit_pips is None:
                return
            if position['type'].value == 'BUY' and self.activate_pips is not None:
                position['sl'] = position['sl'] + (self.activate_pips / 10)
                position['tp'] = position['tp'] + (self.profit_pips / 10)
            else:
                if self.activate_pips is not None:
                    position['sl'] = position['entry'] - (self.activate_pips / 10)
