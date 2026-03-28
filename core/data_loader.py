from pathlib import Path
import pandas as pd

BASE_PATH = Path(r"D:\Trading Forex\GITHUB\QuantTrading\data\historical")

def load_data(symbol="XAUUSD", timeframe="H1", year="2022"):

    path = BASE_PATH / symbol / timeframe / f"{year}.parquet"

    if not path.exists():
        raise FileNotFoundError(f"Data not found: {path}")

    df = pd.read_parquet(path)

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index("time")

    return df