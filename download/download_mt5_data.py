import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# koneksi ke MT5
mt5.initialize()

symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_H1

# === DATA 2022 ===
rates_2022 = mt5.copy_rates_range(
    symbol,
    timeframe,
    datetime(2022, 1, 1),
    datetime(2022, 12, 31)
)

df_2022 = pd.DataFrame(rates_2022)
df_2022['time'] = pd.to_datetime(df_2022['time'], unit='s')

df_2022.to_parquet("data/XAUUSD_2022.parquet")

# === DATA 2023 ===
rates_2023 = mt5.copy_rates_range(
    symbol,
    timeframe,
    datetime(2023, 1, 1),
    datetime(2023, 12, 31)
)

df_2023 = pd.DataFrame(rates_2023)
df_2023['time'] = pd.to_datetime(df_2023['time'], unit='s')

df_2023.to_parquet("data/XAUUSD_2023.parquet")

mt5.shutdown()

print("DONE")