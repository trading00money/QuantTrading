import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os

# =========================
# INIT MT5
# =========================
if not mt5.initialize():
    raise RuntimeError("MT5 tidak terkoneksi")

symbol = "GOLD"
timeframe = mt5.TIMEFRAME_H1

# =========================
# AMBIL DATA
# =========================
rates = mt5.copy_rates_range(
    symbol,
    timeframe,
    datetime(2022, 1, 1),
    datetime(2023, 12, 31)
)

if rates is None or len(rates) == 0:
    raise RuntimeError("Data MT5 kosong — cek koneksi / symbol / history")

df = pd.DataFrame(rates)

print("COLUMNS:", df.columns)

# Handle time column dengan aman
if "time" in df.columns:
    df["time"] = pd.to_datetime(df["time"], unit="s")

elif "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

else:
    raise RuntimeError("Tidak ada kolom waktu di data MT5")

# =========================
# SAVE PATH
# =========================
save_path = r"D:\Trading Forex\GITHUB\QuantTrading\data\historical\GOLD\H1"

os.makedirs(save_path, exist_ok=True)

file_path = os.path.join(save_path, "2022.parquet")

df.to_parquet(file_path)

mt5.shutdown()

print("DONE:", file_path)