#!/usr/bin/env python3
# generate_btcusd_signals.py

import os
import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

# Pastikan project root di sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# =========================
# KONFIGURASI
# =========================
SYMBOL = "BTC/USDT"
TIMEFRAME = "1d"
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
RUN_BACKTEST = True
INITIAL_CAPITAL = 10000.0

# =========================

def load_data_with_fallback(symbol, timeframe, start_date, end_date):
    """Load data historis dengan fallback"""

    # --- CCXT ---
    try:
        import ccxt
        logger.info("Load data via CCXT...")

        exchange = ccxt.binance({'enableRateLimit': True})

        sym = symbol.upper().replace('-', '/')
        if sym == "BTC/USD":
            sym = "BTC/USDT"

        since = int(pd.Timestamp(start_date).timestamp() * 1000)
        ccxt_tf = timeframe

        ohlcv = exchange.fetch_ohlcv(sym, ccxt_tf, since=since, limit=1000)

        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df

    except Exception as e:
        logger.warning(f"CCXT gagal: {e}")

    # --- yfinance ---
    try:
        import yfinance as yf
        logger.info("Load data via yfinance...")

        df = yf.download(symbol, start=start_date, end=end_date)

        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            return df

    except Exception as e:
        logger.warning(f"yfinance gagal: {e}")

    # --- Dummy ---
    logger.warning("Pakai dummy data")

    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    price = 20000 + np.cumsum(np.random.randn(len(dates)))

    df = pd.DataFrame({
        'open': price,
        'high': price * 1.01,
        'low': price * 0.99,
        'close': price,
        'volume': np.random.rand(len(dates))
    }, index=dates)

    return df


async def generate_signal(data, symbol, timeframe):
    """Generate signal"""
    from core.signal_engine import AISignalEngine

    engine = AISignalEngine({})
    return await engine.generate_signal(
        symbol=symbol,
        data=data,
        timeframe=timeframe.upper(),
        current_price=float(data['close'].iloc[-1])
    )


def main():
    print("=" * 50)
    print("BTCUSD SIGNAL GENERATOR")
    print("=" * 50)

    data = load_data_with_fallback(SYMBOL, TIMEFRAME, START_DATE, END_DATE)

    if data is None or data.empty:
        print("Data gagal load")
        return

    print(f"Harga terakhir: {data['close'].iloc[-1]}")

    signal = asyncio.run(generate_signal(data, SYMBOL, TIMEFRAME))
    print(signal)


if __name__ == "__main__":
    main()