from datetime import datetime, timedelta

from capital.epics import Epics
from capital.get_epic_by_name import get_epic_by_name
from capital.historical_candles import (
    get_historical_candles,
    get_historical_data_looped,
)
from capital.login import login
from capital.resolutions import Resolutions
from config import API_KEY, API_PASSWORD, EMAIL_ACCOUNT

if __name__ == "__main__":
    headers, _, _, _ = login(EMAIL_ACCOUNT, API_PASSWORD, API_KEY)
    start = datetime(2025, 4, 13, 22, 0) - timedelta(hours=4)
    until = datetime.now() - timedelta(hours=4)
    
    df = get_historical_data_looped(
        headers=headers,
        epic=Epics.GOLD,
        resolution=Resolutions.MINUTE_1,
        from_dt=start,
        until_dt=until,
        save_to_csv=True
    )
    df.to_csv("history/gold_minute_1_14_18_30_18_04.csv", index=False)
