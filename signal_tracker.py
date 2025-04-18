from utils.message_formatter import format_confirmation_alert, format_rejection_alert
from utils.telegram_alert import send_telegram_alert


class SignalTracker:
    def __init__(self):
        self.pending_confirmation = None

    def register_anticipate_signal(self, signal_row, signal_type):
        self.pending_confirmation = {
            "signal": signal_row,
            "type": signal_type,
            "confirmed": False
        }


    def check_confirmation(self, current_row, early_confirmation: bool = False) -> bool | None:
        if not self.pending_confirmation:
            return None

        if self.pending_confirmation["confirmed"]:
            return None

        signal = self.pending_confirmation["signal"]
        _type = self.pending_confirmation["type"]
        entry_price = signal["close"]
        confirm_price = current_row["close"]

        if (
            (_type == "BUY" and confirm_price > entry_price) or
            (_type == "SELL" and confirm_price < entry_price)
        ):
            # Confirmar señal
            msg = format_confirmation_alert(_type, confirm_price, current_row["time"], early_confirmation)
            send_telegram_alert(msg)
            self.pending_confirmation["confirmed"] = True
            print(f"Confirmed signal: {_type} at {current_row['time']}")
            return True
        else:
            msg = format_rejection_alert(
                self.pending_confirmation["type"],
                self.pending_confirmation["signal"]["close"],
                self.pending_confirmation["signal"]["time"],
                early_confirmation
            )
            send_telegram_alert(msg)
            return False