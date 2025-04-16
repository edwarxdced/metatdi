import requests
import pandas as pd
from datetime import datetime, timedelta
from capital.epics import Epics
from capital.resolutions import Resolutions
from typing import Dict, Any, Optional
from time import sleep
from datetime import timezone
def get_historical_candles(
    headers: Dict[str, Any],
    epic=Epics.GOLD,
    resolution=Resolutions.MINUTE_15,
    limit:int=200,
    from_dt: Optional[datetime] = None,
    )->tuple[datetime, pd.DataFrame]:
    
    url = f"https://demo-api-capital.backend-capital.com/api/v1/prices/{epic.value}"
    
    params = {
        "resolution": resolution.value,
        "max": limit
    }
    if from_dt:
        params["from"] = from_dt.isoformat()
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    candles = []
    last_time = datetime.fromisoformat(data['prices'][-1]['snapshotTime'])
    for item in data['prices']:
        candles.append({
            'time': datetime.fromisoformat(item['snapshotTime']).replace(tzinfo=timezone.utc),
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

    while current_from < until_dt:
        print(f"⬇️  Descargando desde {current_from}...")

        last_time, partial_df = get_historical_candles(
            headers=headers,
            epic=epic,
            resolution=resolution,
            limit=1000,
            from_dt=current_from
        )

        if partial_df.empty:
            print("⚠️ No se encontraron datos. Deteniendo.")
            break

        df_list.append(partial_df)
        current_from = last_time
        
        if last_time >= until_dt:
            break
        sleep(1)

    full_df = pd.concat(df_list).drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)

    print(f"✅ Total velas descargadas: {len(full_df)}")

    if save_to_csv:
        name = f"{epic.value}_{resolution.value}.csv".lower()
        full_df.to_csv(f"history/{name}", index=False)
        print(f"💾 Datos guardados en: history/{name}")

    return full_df


