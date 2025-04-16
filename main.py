from capital.historical_candles import get_historical_data_looped, get_historical_candles
from capital.epics import Epics
from capital.resolutions import Resolutions
from capital.login import login
from datetime import datetime, timezone
from config import EMAIL_ACCOUNT, API_PASSWORD, API_KEY
from capital.get_epic_by_name import get_epic_by_name

if __name__ == "__main__":
    headers, _, _, _ = login(EMAIL_ACCOUNT, API_PASSWORD, API_KEY)

    #2025-04-01 16:40:00+00:00,3132.69,3132.79,3132.15,3132.54,145
    df = get_historical_data_looped(
        headers=headers,
        epic=Epics.GOLD,
        resolution=Resolutions.MINUTE_1,
        from_dt=datetime(2025, 4, 1, 12, 00),
        until_dt=datetime(2025, 4, 1, 20, 20),
        save_to_csv=False
    )
    df.to_csv("history/back.csv", index=False)
    breakpoint()