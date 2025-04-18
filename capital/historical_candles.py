from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Any, Dict, Optional

import pandas as pd
import requests

from capital.epics import Epics
from capital.resolutions import Resolutions


def minutes_until_next_0045(from_dt: datetime) -> int:
    """
    Returns the number of minutes from the given datetime until 00:45 AM the next day.
    """
    next_day = from_dt + timedelta(days=1)
    target_time = next_day.replace(hour=0, minute=45, second=0, microsecond=0)
    delta = target_time - from_dt
    return int(delta.total_seconds() / 60)


def get_historical_candles(
    headers: Dict[str, Any],
    epic=Epics.GOLD,
    resolution=Resolutions.MINUTE_15,
    limit:int = 200,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    )->tuple[datetime, pd.DataFrame]:
    
    url = f"https://demo-api-capital.backend-capital.com/api/v1/prices/{epic.value}"
    
    params = {
        "resolution": resolution.value,
        "max": limit
    }
    if from_dt:
        params["from"] = from_dt.isoformat()
    if to_dt:
        params["to"] = to_dt.isoformat()
    
    print(f"Searching with {params}")
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    candles = []
    started_time = datetime.fromisoformat(data['prices'][0]['snapshotTime'])
    last_time = datetime.fromisoformat(data['prices'][-1]['snapshotTime'])
    print(f"Resulting from {started_time} to {last_time}")

    for item in data['prices']:
        candles.append({
            'time': datetime.fromisoformat(item['snapshotTime']) - timedelta(hours=4),
            'open': item['openPrice']['bid'],
            'high': item['highPrice']['bid'],
            'low': item['lowPrice']['bid'],
            'close': item['closePrice']['bid'],
            'volume': item['lastTradedVolume']
        })
    return last_time, pd.DataFrame(candles)


def get_historical_data_looped(
    headers: Dict[str, Any],
    epic: Epics,   
    resolution: Resolutions,
    from_dt: datetime,
    until_dt: datetime,
    save_to_csv: bool = False
) -> pd.DataFrame:
    df_list = []
    current_from = from_dt
    until_dt = until_dt
    print(f"Start downloading from {current_from} to {until_dt}")

    while current_from < until_dt:
        print(f"⬇️  Downloading from {current_from}...")

        try:
            last_time, partial_df = get_historical_candles(
                headers=headers,
                epic=epic,
                resolution=resolution,
                limit=1000,
                from_dt=current_from
            )
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            break

        if partial_df.empty:
            print("⚠️ No data found. Stopping.")
            break
        
        try:
            df_list.append(partial_df)
            current_from = last_time
        except Exception as e:
            print(f"❌ Error appending data: {e}")
            breakpoint()
        
        if last_time >= until_dt:
            break

        sleep(1)
    full_df = pd.concat(df_list).drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)

    print(f"✅ Total candles downloaded: {len(full_df)}")
    print(f"Downloaded from {full_df.iloc[0]['time']} to {full_df.iloc[-1]['time']}")

    if save_to_csv:
        name = f"{epic.value}_{resolution.value}.csv".lower()
        full_df.to_csv(f"history/{name}", index=False)
        print(f"💾 Data saved in: history/{name}")

    return full_df


def get_historical_data_looped_with_limit(
    headers: Dict[str, Any],
    epic: Epics,
    resolution: Resolutions,
    from_dt: datetime,
    limit: int = 1000,
    save_to_csv: bool = False
) -> pd.DataFrame:
    df_list = []

    minutes = minutes_until_next_0045(from_dt)
    print(f"Minutes until next 00:45: {minutes}")
    if minutes > 1000:
        minutes = 1000
    last_time, partial_df = get_historical_candles(
        headers=headers,
        epic=epic,
        resolution=resolution,
        from_dt=from_dt,
        limit=minutes,
    )

    breakpoint()

    if partial_df.empty:
        print("⚠️ No data found. Stopping.")
        return pd.DataFrame()

    last_time = partial_df.iloc[0]['time']
    df_list.append(partial_df)
    breakpoint()

    while True:
        print(f"⬇️  Downloading from {last_time}...")

        try:
            _, partial_df = get_historical_candles(
                headers=headers,
                epic=epic,
                resolution=resolution,
                limit=limit,
                to_dt=last_time
            )
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            break

        if partial_df.empty:
            print("⚠️ No data found. Stopping.")
            break
        
        last_time = partial_df.iloc[0]['time']
        df_list.append(partial_df)\
        
        if last_time < from_dt:
            breakpoint()
            break

    full_df = pd.concat(df_list).drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)

    print(f"✅ Total candles downloaded: {len(full_df)}")
    print(f"Downloaded from {full_df.iloc[0]['time']} to {full_df.iloc[-1]['time']}")

    if save_to_csv:
        name = f"{epic.value}_{resolution.value}.csv".lower()
        full_df.to_csv(f"history/{name}", index=False)
        print(f"💾 Data saved in: history/{name}")

    return full_df
    

