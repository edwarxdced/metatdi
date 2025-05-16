from datetime import datetime
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd # type: ignore

from config import BALANCE, BREAK_EVEN_TRIGGER, LOT_SIZE, TRAILING_DISTANCE
from core.position_components.break_even_manager import BreakEvenManager
from core.position_components.secure_level_manager import SecureLevelManager
from core.position_components.trailing_stop_manager import TrailingStopManager
from enums.entry_context import EntryContext
from enums.type_signals import TypeSignal
from utils.logger import get_logger


def dollars_to_pips(dollar_amount: float, lot_size: float) -> float:
    """
    Convert dollars to pips in XAUUSD.

    Each pip (0.1 of movement) is worth:
    - 10 USD per 1.0 lot
    - 1 USD per 0.1 lot
    - 0.1 USD per 0.01 lot
    """
    pip_value_per_lot = 10  # 10 USD by pip in 1.0 lot in XAUUSD
    pip_value = pip_value_per_lot * lot_size
    pips = dollar_amount / pip_value
    return pips


class PositionManager:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.active_position: Optional[Dict[str, Any]] = None
        self.closed_positions: List[Dict[str, Any]] = []
        self.balance: float = BALANCE
        self.balance_initial: float = BALANCE
        self.lot_size: float = LOT_SIZE
        self.work_mode: str = 'V2'

        self.break_even_manager: Optional[BreakEvenManager] = None
        self.trailing_stop_manager: Optional[TrailingStopManager] = None
        self.secure_level_manager: Optional[SecureLevelManager] = None

    def open_position(
        self,
        trade_type: TypeSignal,
        entry_price: float,
        tp: float,
        sl: float,
        time: datetime,
        lot_size: float = LOT_SIZE,
        entry_context: EntryContext = EntryContext.STANDARD
    ) -> None:
        if self.active_position is not None:
            self.logger.error("Position already open. Cannot open new position.")
            self.logger.info(f"Active position: {self.active_position.get('type')}")
            return

        quantity = lot_size * self.balance
        self.balance -= quantity
        self.active_position = {
            "type": trade_type,
            "entry": entry_price,
            "entry_sl": sl,
            "entry_tp": tp,
            "sl": sl,
            "tp": tp,
            "sl_break_even": None,
            "tp_break_even": None,
            "sl_trail": None,
            "tp_trail": None,
            "status": "open",
            "trail_active": False,
            "breakeven_applied": False,
            "max_price": entry_price,
            "min_price": entry_price,
            "open_time": time,
            "lot_size": lot_size,
            "entry_context": entry_context,
            "reason": "",
            "balance": self.balance,
            "quantity": quantity,
        }

        self.break_even_manager = BreakEvenManager(multi_level=False)
        activate_pips = dollars_to_pips(60, lot_size)
        profit_pips = dollars_to_pips(100, lot_size)
        self.break_even_manager.set_normal(activate_pips=activate_pips, profit_pips=profit_pips)
        self.logger.info(f"Opened {trade_type.value} Entry: {entry_price} TP: {tp} SL: {sl} Time: {time}")

    def update_position_v1(self, price: float, time: datetime) -> bool:
        pos = self.active_position
        if not pos or pos["status"] != "open":
            return False
    
        pos["max_price"] = max(pos["max_price"], price)
        pos["min_price"] = min(pos["min_price"], price)
        current_sl = pos["sl_trail"] or pos["sl_break_even"] or pos["sl"]
        current_tp = pos["tp_trail"] or pos["tp_break_even"] or pos["tp"]
        
        if not pos["breakeven_applied"] and self.check_break_even(price, time):
            return True

        if pos["breakeven_applied"] and self.check_trailing_stop(price):
            return True

        if self.check_sl_hit(price, time, current_sl):
            return True

        if self.check_tp_hit(price, time, current_tp):
            return True
        
        return False
    
    def update_position_v2(self, price: float, time: datetime) -> bool:
        pos = self.active_position
        if not pos or pos["status"] != "open":
            return False

        current_profit_pips = self.calculate_profit_pips(pos, price)
        # apply Break Even
        if self.break_even_manager and self.break_even_manager.should_apply(current_profit_pips):
            self.break_even_manager.apply(pos, price)
            self.logger.info(
                f"Break-even applied. Current Price: {price} New TP: {pos['tp']} New SL: {pos['sl']} Time: {time}"
            )

        if (pos["type"].value == "BUY" and price < pos["sl"]) or (pos["type"].value == "SELL" and price > pos["sl"]):
            pos["status"] = "closed"
            pos["exit_price"] = price
            pos["exit_time"] = time
            pos["exit_reason"] = "SL"
            self.close_position(price, time, reason="SL")
            self.active_position = None
            self.logger.info(f"Position closed due to SL at {price} Time: {time}")
            return True

        elif (
            (pos["type"].value == "BUY" and price > pos["tp"]) or (pos["type"].value == "SELL" and price < pos["tp"])
        ):
            pos["status"] = "closed"
            pos["exit_price"] = price
            pos["exit_time"] = time
            pos["exit_reason"] = "TP"
            self.close_position(price, time, reason="TP")
            self.active_position = None
            self.logger.info(f"Position closed due to TP at {price} Time: {time}")
            return True

        return False

    def update_position(self, price: float, time: datetime) -> bool:
        """
        Update the position based on the work mode.
        V1: Standard mode
        V2: Advanced mode
        Args:
            price (float): current price of the market
            time (datetime): current time of the market

        Returns:
            bool: True if the position is updated, False otherwise
        """
        pos = self.active_position
        if not pos or pos["status"] != "open":
            return False
        
        if self.work_mode == 'V1':
            return self.update_position_v1(price, time)
        elif self.work_mode == 'V2':
            return self.update_position_v2(price, time)
        return False

    def calculate_profit_pips(self, pos: Dict[str, Any], current_price: float) -> float:
        """ Calculate the profit in pips.
        In XAUUSD 1 pip = 0.1 of price.

        Args:
            pos (Dict[str, Any]): position data
            current_price (float): current price of the market

        Returns:
            float: profit in pips
        """
        if pos["type"].value == "BUY":
            diff = current_price - pos["entry"]
        else:
            diff = pos["entry"] - current_price
        return diff / 0.1  # 1 pip = 0.1 movement

    def check_sl_hit(self, price: float, time: datetime, sl: float) -> bool:
        """ Check if the SL is hit.

        Args:
            price (float): current price of the market
            time (datetime): current time of the market
            sl (float): stop loss price

        Returns:
            bool: True if the SL is hit, False otherwise
        """
        if not self.active_position:
            return False
        
        pos = self.active_position
        if pos["type"] == TypeSignal.BUY and price <= sl:
            self.close_position(price, time, reason="SL")
            return True
        
        if pos["type"] == TypeSignal.SELL and price >= sl:
            self.close_position(price, time, reason="SL")
            return True
        return False

    def check_tp_hit(self, price: float, time: datetime, tp: float) -> bool:
        """ Check if the TP is hit.

        Args:
            price (float): current price of the market
            time (datetime): current time of the market
            tp (float): take profit price

        Returns:
            bool: True if the TP is hit, False otherwise
        """
        if not self.active_position:
            return False
        pos = self.active_position
        
        if pos["type"] == TypeSignal.BUY and price >= tp:
            self.close_position(price, time, reason="TP")
            return True
        
        if pos["type"] == TypeSignal.SELL and price <= tp:
            self.close_position(price, time, reason="TP")
            return True
        return False

    def check_break_even(self, price: float, time: datetime) -> bool:
        """ Check if the break even is hit.

        Args:
            price (float): current price of the market
            time (datetime): current time of the market

        Returns:
            bool: True if the break even is hit, False otherwise
        """
        
        if not self.active_position:
            return False
        
        pos = self.active_position
        trigger_price = pos["entry"] + BREAK_EVEN_TRIGGER
        if pos["type"] == TypeSignal.SELL:
            trigger_price = pos["entry"] - BREAK_EVEN_TRIGGER

        if (
            (pos["type"] == TypeSignal.BUY and price >= trigger_price) or
            (pos["type"] == TypeSignal.SELL and price <= trigger_price)
        ):
            pos["sl_break_even"] = pos["entry"]
            pos["tp_break_even"] = pos["tp"] + BREAK_EVEN_TRIGGER
            if pos["type"] == TypeSignal.SELL:
                pos["tp_break_even"] = pos["tp"] - BREAK_EVEN_TRIGGER

            pos["breakeven_applied"] = True
            self.logger.info(
                f"Break-even applied. New SL: {pos['sl_break_even']} New TP: {pos['tp_break_even']} Time: {time}"
            )
            return True
        return False

    def check_trailing_stop(self, price: float) -> bool:
        """ Check if the trailing stop is hit.

        Args:
            price (float): current price of the market

        Returns:
            bool: True if the trailing stop is hit, False otherwise
        """
        if not self.active_position:
            return False
        pos = self.active_position
        base_sl = pos["sl_trail"] or pos["sl_break_even"] or pos["sl"]
        trail_trigger = base_sl + TRAILING_DISTANCE if pos["type"] == TypeSignal.BUY else base_sl - TRAILING_DISTANCE
        if (
            (pos["type"] == TypeSignal.BUY and price >= trail_trigger) or
            (pos["type"] == TypeSignal.SELL and price <= trail_trigger and price < pos["entry"])
        ):
            pos["sl_trail"] = pos["entry"]
            pos["tp_trail"] = pos["tp"] + TRAILING_DISTANCE
            if pos["type"] == TypeSignal.SELL:
                pos["tp_trail"] = pos["tp"] - TRAILING_DISTANCE
            pos["trail_active"] = True
            self.logger.info(f"Trailing stop updated. New SL: {pos['sl_trail']} New TP: {pos['tp_trail']}")
            return True
        return False

    def close_position(self, price: float, time: datetime, reason: str) -> None:
        """ Close the current position.

        Args:
            price (float): current price of the market
            time (datetime): current time of the market
            reason (str): reason for closing the position
        """
        if not self.active_position:
            return
        
        pos = self.active_position
        pos["status"] = "closed"
        pos["exit_price"] = price
        pos["exit_time"] = time
        pos["exit_reason"] = reason
        if pos["type"] == TypeSignal.BUY:
            profit = (price - pos["entry"]) * 100 * pos["lot_size"]
        else:
            profit = (pos["entry"] - price) * 100 * pos["lot_size"]
        
        self.balance += (pos["quantity"] + profit)
        pos["profit"] = profit
        pos["balance"] = self.balance
        self.closed_positions.append(pos)
        self.logger.info(
            "Position Closed({}) due to {} Close: {} Open: {} Time: {} Profit: {}".format(
                pos["type"].value,
                reason,
                price,
                pos["entry"],
                time,
                profit
            )
        )
        self.active_position = None

    def force_close_position(self, price: float, time: datetime, reason: str) -> None:
        if self.active_position and self.active_position["status"] == "open":
            self.close_position(price, time, reason)

    def analyze_closed_positions(self) -> Dict[str, Any]:
        if not self.closed_positions:
            return {}

        total_trades = len(self.closed_positions)
        wins = 0
        losses = 0
        total_profit = 0.0
        total_loss = 0.0
        profits = []
        losses_list = []

        for pos in self.closed_positions:
            profit = pos["profit"]

            if profit >= 0:
                wins += 1
                profits.append(profit)
                total_profit += profit
            else:
                losses += 1
                losses_list.append(profit)
                total_loss += profit

        winrate = (wins / total_trades) * 100 if total_trades > 0 else 0
        avg_win = np.mean(profits) if profits else 0.0
        avg_loss = np.mean(losses_list) if losses_list else 0.0
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else np.inf
        expectancy = (winrate / 100) * avg_win + ((1 - winrate / 100) * avg_loss)

        balance_final_absolute = self.balance - self.balance_initial
        balance_final_percent = balance_final_absolute / self.balance_initial * 100
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "winrate_percent": winrate,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "net_profit": total_profit + total_loss,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "expectancy_per_trade": expectancy,
            "balance_initial": self.balance_initial,
            "balance_final": self.balance,
            "balance_final_percent": balance_final_percent,
            "balance_final_absolute": balance_final_absolute,
        }

    def export_closed_positions_to_dataframe(self) -> pd.DataFrame:
        if not self.closed_positions:
            return pd.DataFrame()

        data = {
            "entry_time": [pos["open_time"] for pos in self.closed_positions],
            "exit_time": [pos["exit_time"] for pos in self.closed_positions],
            "type": [pos["type"].value for pos in self.closed_positions],
            "entry_price": [pos["entry"] for pos in self.closed_positions],
            "entry_sl": [pos["entry_sl"] for pos in self.closed_positions],
            "entry_tp": [pos["entry_tp"] for pos in self.closed_positions],
            "exit_price": [pos["exit_price"] for pos in self.closed_positions],
            "exit_reason": [pos["exit_reason"] for pos in self.closed_positions],
            "lot_size": [pos["lot_size"] for pos in self.closed_positions],
            "breakeven_applied": [pos["breakeven_applied"] for pos in self.closed_positions],
            "trail_active": [pos["trail_active"] for pos in self.closed_positions],
            "sl_break_even": [pos["sl_break_even"] for pos in self.closed_positions],
            "tp_break_even": [pos["tp_break_even"] for pos in self.closed_positions],
            "sl_trail": [pos["sl_trail"] for pos in self.closed_positions],
            "tp_trail": [pos["tp_trail"] for pos in self.closed_positions],
            "max_price": [pos["max_price"] for pos in self.closed_positions],
            "min_price": [pos["min_price"] for pos in self.closed_positions],
            "entry_context": [pos["entry_context"].value for pos in self.closed_positions],
        }
        return pd.DataFrame(data)
