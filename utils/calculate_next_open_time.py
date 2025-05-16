from datetime import datetime, timedelta


def get_next_open_time(current_time: datetime, timeframe_minutes: int) -> datetime:
    minute = current_time.minute
    remainder = minute % timeframe_minutes
    if remainder == 0 and current_time.second == 0 and current_time.microsecond == 0:
        return current_time + timedelta(minutes=timeframe_minutes)
    minutes_to_add = timeframe_minutes - remainder
    return current_time.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
