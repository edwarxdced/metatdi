import pandas as pd


def normalize_csv_from_mt5(file_path: str, columns: list[str]) -> None:
    df = pd.read_csv(file_path, header=None)
    df.columns = columns
    df['time'] = pd.to_datetime(df['time'])
    df.to_csv(file_path, index=False)


def normalize_from_ohlcv_to_ticks(file_path: str, output_path: str = "history/gold_ticks.csv") -> None:
    df = pd.read_csv(file_path)

    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'] - pd.Timedelta(hours=3)
    data = []
    columns = ['open', 'high', 'low', 'close']
    for _, row in df.iterrows():
        time = row['time']
        for col in columns:
            data.append([time, row[col]])

    ticks_df = pd.DataFrame(data, columns=['time', 'tick'])
    ticks_df.to_csv(output_path, index=False)
