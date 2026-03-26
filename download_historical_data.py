#!/usr/bin/env python3
"""
download_historical_data.py

Download data historis BTC/USDT (dan pair lain) minimal 3 tahun.

CARA JALANKAN:
python download_historical_data.py

SUMBER DATA (urutan prioritas):
1. CCXT (Binance)   — Gratis, tanpa API key, data paling lengkap
2. yfinance          — Gratis, tanpa API key, cukup untuk daily
3. CoinGecko API     — Gratis, tanpa API key, fallback terakhir

INSTALL DEPENDENCY:
pip install ccxt yfinance requests pandas

OUTPUT:
data/historical/BTC/USDT_1d_2021-01-01_2025-01-01.csv
data/historical/BTC/USDT_1d_2021-01-01_2025-01-01.parquet  (opsional)
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# KONFIGURASI — Ubah sesuai kebutuhan
# ============================================================

CONFIGS = [
    {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "start_date": "2021-01-01",
        "end_date": "2025-01-01",
    },
]

DATA_DIR = "data/historical"

SAVE_CSV = True
SAVE_PARQUET = True


# ============================================================
# HELPER: Normalisasi symbol
# ============================================================

def normalize_symbol(symbol: str, source: str) -> str:
    """
    Konversi symbol ke format yang dikenali oleh setiap source.

    Input bisa: "BTC/USDT", "BTCUSD", "BTC/USDT", "BTC/USD"
    """
    sym = symbol.upper().strip()

    if source == "ccxt":
        sym = sym.replace("-", "/")
        if sym == "BTC/USD":
            return "BTC/USDT"
        if "/" not in sym:
            for quote in ["USDT", "BUSD", "USDC", "USD"]:
                if sym.endswith(quote):
                    return f"{sym[:-len(quote)]}/{quote}"
        return sym

    elif source == "yfinance":
        sym = sym.replace("/", "-")
        if sym in ["BTCUSDT", "BTC/USDTT"]:
            return "BTC/USDT"
        if "-" not in sym:
            for quote in ["USDT", "USD"]:
                if sym.endswith(quote):
                    return f"{sym[:-len(quote)]}-USD"
        return sym

    elif source == "coingecko":
        coin_map = {
            "BTC": "bitcoin", "ETH": "ethereum"
        }
        base = sym.split("-")[0].split("/")[0].replace("USDT", "").replace("USD", "")
        return coin_map.get(base, base.lower())

    return sym


def normalize_timeframe(timeframe: str, source: str) -> str:
    """Konversi timeframe ke format source."""
    tf_map = {
        "ccxt": {"1d": "1d"},
        "yfinance": {"1d": "1d"},
    }
    return tf_map.get(source, {}).get(timeframe, timeframe)


# ============================================================
# CCXT
# ============================================================

def download_via_ccxt(symbol, timeframe, start_date, end_date):
    """
    Download via CCXT library (Binance)
    """
    try:
        import ccxt
    except ImportError:
        print("  ⚠ ccxt belum terinstall.")
        return None

    exchange = ccxt.binance({'enableRateLimit': True})

    ccxt_symbol = normalize_symbol(symbol, "ccxt")

    since = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)

    all_candles = []

    while since < end_ts:
        candles = exchange.fetch_ohlcv(ccxt_symbol, timeframe, since=since, limit=1000)
        if not candles:
            break
        all_candles.extend(candles)
        since = candles[-1][0] + 1

    if not all_candles:
        return None

    df = pd.DataFrame(all_candles, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_data(df: pd.DataFrame, symbol: str) -> dict:
    """
    Validasi kualitas data
    """
    issues = []

    nan_counts = df.isna().sum()
    if nan_counts.sum() > 0:
        issues.append("NaN detected")

    return {
        "symbol": symbol,
        "bars": len(df),
        "issues": issues,
        "valid": len(issues) == 0
    }


# ============================================================
# SAVE
# ============================================================

def save_data(df, symbol, timeframe, start_date, end_date, data_dir):
    """Simpan data"""
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    base = f"{symbol}_{timeframe}_{start_date}_{end_date}"

    if SAVE_CSV:
        df.to_csv(f"{data_dir}/{base}.csv")

    if SAVE_PARQUET:
        try:
            df.to_parquet(f"{data_dir}/{base}.parquet")
        except:
            pass


# ============================================================
# LOAD
# ============================================================

def load_historical_data(symbol="BTC/USDT", timeframe="1d",
                         start_date="2021-01-01", end_date="2025-01-01",
                         data_dir=DATA_DIR):
    """
    Load data historis
    """
    base = f"{symbol}_{timeframe}_{start_date}_{end_date}"

    parquet_path = f"{data_dir}/{base}.parquet"
    if os.path.exists(parquet_path):
        return pd.read_parquet(parquet_path)

    csv_path = f"{data_dir}/{base}.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path, index_col='timestamp', parse_dates=True)

    return None


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("DOWNLOAD DATA")
    print("=" * 60)

    for cfg in CONFIGS:
        df = download_via_ccxt(
            cfg["symbol"],
            cfg["timeframe"],
            cfg["start_date"],
            cfg["end_date"]
        )

        if df is None:
            print("Gagal download")
            continue

        report = validate_data(df, cfg["symbol"])
        print(report)

        save_data(
            df,
            cfg["symbol"],
            cfg["timeframe"],
            cfg["start_date"],
            cfg["end_date"],
            DATA_DIR
        )

    print("DONE")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()