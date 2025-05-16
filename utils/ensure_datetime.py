from datetime import datetime

import pandas as pd


def ensure_datetime(ts) -> datetime:
    """
    Convierte un timestamp numpy.datetime64, pandas.Timestamp o str a datetime.datetime.
    """
    if isinstance(ts, datetime):
        return ts
    return pd.to_datetime(ts).to_pydatetime()
