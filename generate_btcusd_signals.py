# #!/usr/bin/env python3
“””
generate_btcusd_signals.py

Script standalone untuk generate signal BTCUSD dari data historis.

CARA PAKAI:
1. Simpan file ini di ROOT PROJECT (sejajar dengan run.py)
2. Jalankan: python generate_btcusd_signals.py

KONFIGURASI:
Ubah variabel di bagian KONFIGURASI di bawah.

OUTPUT:
- Signal terakhir (BUY/SELL/HOLD + confidence)
- Level entry, SL, TP
- Komponen per-engine (Gann, Ehlers, Astro, ML, Pattern)
- Opsional: jalankan backtest penuh
“””

import os
import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

# Pastikan project root di sys.path

PROJECT_ROOT = os.path.dirname(os.path.abspath(**file**))
sys.path.insert(0, PROJECT_ROOT)

# ============================================================

# KONFIGURASI — Ubah sesuai kebutuhan Anda

# ============================================================

SYMBOL = “BTC-USD”           # Symbol untuk Yahoo Finance / CCXT
TIMEFRAME = “1d”             # 1d, 4h, 1h, 15m, 5m
START_DATE = “2023-01-01”    # Awal data historis
END_DATE = “2024-01-01”      # Akhir data historis (None = hari ini)
RUN_BACKTEST = True          # True = jalankan backtest juga
INITIAL_CAPITAL = 10000.0    # Modal awal backtest

# ============================================================

def load_data_with_fallback(symbol, timeframe, start_date, end_date):
“””
Load data historis dengan multiple fallback:
1. CCXT (Binance) jika tersedia
2. yfinance jika tersedia
3. Dummy data untuk testing
“””
# — Coba CCXT (Binance) —
try:
import ccxt
logger.info(“Mencoba load data via CCXT (Binance)…”)
exchange = ccxt.binance({‘enableRateLimit’: True})

```
    # Normalize symbol: "BTC-USD" → "BTC/USDT"
    sym = symbol.upper().replace('-', '/')
    if sym == "BTC/USD":
        sym = "BTC/USDT"  # Binance pakai USDT
    
    since = int(pd.Timestamp(start_date).timestamp() * 1000)
    tf_map = {'1d': '1d', '4h': '4h', '1h': '1h', '15m': '15m', '5m': '5m'}
    ccxt_tf = tf_map.get(timeframe, '1d')
    
    all_data = []
    end_ts = int(pd.Timestamp(end_date or datetime.now()).timestamp() * 1000)
    
    while since < end_ts:
        ohlcv = exchange.fetch_ohlcv(sym, ccxt_tf, since=since, limit=1000)
        if not ohlcv:
            break
        all_data.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        if len(all_data) > 10000:  # Safety limit
            break
    
    if all_data:
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        if end_date:
            df = df[df.index <= end_date]
        logger.success(f"Data loaded via CCXT (Binance): {len(df)} bars")
        return df
except ImportError:
    logger.info("ccxt tidak terinstall. Coba: pip install ccxt")
except Exception as e:
    logger.info(f"CCXT gagal: {e}")

# --- Coba yfinance ---
try:
    import yfinance as yf
    logger.info("Mencoba load data via yfinance...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date or datetime.now().strftime('%Y-%m-%d'))
    
    if df is not None and not df.empty:
        df.columns = [c.lower() for c in df.columns]
        # Drop kolom yang tidak perlu
        drop_cols = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        logger.success(f"Data loaded via yfinance: {len(df)} bars")
        return df
except ImportError:
    logger.info("yfinance tidak terinstall. Coba: pip install yfinance")
except Exception as e:
    logger.info(f"yfinance gagal: {e}")

# --- Fallback: generate dummy data ---
logger.warning("=" * 50)
logger.warning("MENGGUNAKAN DUMMY DATA UNTUK TESTING!")
logger.warning("Untuk data real, install: pip install ccxt yfinance")
logger.warning("=" * 50)

np.random.seed(42)
dates = pd.date_range(start=start_date, end=end_date or datetime.now(), freq='D')
n = len(dates)

# Simulasi harga BTC yang realistis
returns = np.random.randn(n) * 0.025  # 2.5% daily vol
price = 20000 * np.exp(np.cumsum(returns))

df = pd.DataFrame({
    'open': price * (1 + np.random.randn(n) * 0.005),
    'high': price * (1 + abs(np.random.randn(n) * 0.015)),
    'low': price * (1 - abs(np.random.randn(n) * 0.015)),
    'close': price,
    'volume': np.random.uniform(1e9, 5e10, n),
}, index=dates)
df.index.name = 'timestamp'

return df
```

async def generate_signal(data, symbol, timeframe):
“”“Generate signal menggunakan AISignalEngine.”””
from core.signal_engine import AISignalEngine

```
engine = AISignalEngine({})
signal = await engine.generate_signal(
    symbol=symbol,
    data=data,
    timeframe=timeframe.upper(),
    current_price=float(data['close'].iloc[-1])
)
return signal
```

def print_signal_report(signal):
“”“Print signal report yang mudah dibaca.”””
sig = signal.to_dict()

```
direction = sig['signal']
if 'BUY' in direction:
    emoji, color_word = '🟢', 'BULLISH'
elif 'SELL' in direction:
    emoji, color_word = '🔴', 'BEARISH'
else:
    emoji, color_word = '⚪', 'NEUTRAL'

print(f"\n{'=' * 60}")
print(f"  {emoji}  SIGNAL: {direction} ({color_word})")
print(f"{'=' * 60}")
print(f"  Confidence:    {sig['confidence']}%")
print(f"  Strength:      {sig['strength']}")
print(f"  Entry Price:   ${sig['entry_price']:>12,.2f}")
print(f"  Stop Loss:     ${sig['stop_loss']:>12,.2f}")
print(f"  Take Profit:   ${sig['take_profit']:>12,.2f}")
print(f"  Risk/Reward:   {sig['risk_reward']:>12.2f}")

# Component breakdown
print(f"\n  {'─' * 52}")
print(f"  {'Engine':>10} │ {'Signal':>8} │ {'Conf':>5} │ {'Weight':>6} │ Status")
print(f"  {'─' * 52}")
for comp in sig.get('components', []):
    status = '✓ OK' if comp['error'] is None else f"✗ {comp['error'][:20]}"
    print(f"  {comp['source']:>10} │ {comp['signal']:>8} │ {comp['confidence']:>4.0f}% │ {comp['weight']:>5.2f} │ {status}")
print(f"  {'─' * 52}")

# Model attribution
if sig.get('model_attribution'):
    print(f"\n  Model Attribution:")
    for source, pct in sig['model_attribution'].items():
        bar = '█' * int(pct / 5)
        print(f"    {source:>8}: {bar} {pct:.1f}%")

# Reasons
if sig.get('reasons'):
    print(f"\n  Alasan Signal:")
    for reason in sig['reasons']:
        print(f"    → {reason}")

# Errors
if sig.get('errors'):
    print(f"\n  ⚠️  Errors:")
    for err in sig['errors']:
        print(f"    ✗ {err}")
```

def run_simple_backtest(data):
“”“Backtest sederhana tanpa dependensi backtester modul.”””
print(f”\n{’=’ * 60}”)
print(f”  BACKTEST SEDERHANA (per-bar signal)”)
print(f”{’=’ * 60}”)

```
from core.signal_engine import AISignalEngine
engine = AISignalEngine({})

capital = INITIAL_CAPITAL
position = None
trades = []
min_bars = 50

if len(data) < min_bars:
    print(f"  Data terlalu sedikit ({len(data)} bars, min {min_bars})")
    return

# Untuk setiap window 50-bar, generate signal
step = max(1, len(data) // 20)  # ~20 checkpoints
checkpoints = list(range(min_bars, len(data), step))

print(f"  Checking {len(checkpoints)} time points...")

for i in checkpoints:
    window = data.iloc[:i]
    try:
        sig = asyncio.run(engine.generate_signal(
            symbol=SYMBOL, data=window,
            timeframe=TIMEFRAME.upper(),
            current_price=float(window['close'].iloc[-1])
        ))
        
        current_price = float(window['close'].iloc[-1])
        
        # Exit logic
        if position is not None:
            if position['side'] == 'long':
                if current_price <= position['stop_loss']:
                    pnl = (position['stop_loss'] - position['entry']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'SL'})
                    position = None
                elif current_price >= position['take_profit']:
                    pnl = (position['take_profit'] - position['entry']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'TP'})
                    position = None
            elif position['side'] == 'short':
                if current_price >= position['stop_loss']:
                    pnl = (position['entry'] - position['stop_loss']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'SL'})
                    position = None
                elif current_price <= position['take_profit']:
                    pnl = (position['entry'] - position['take_profit']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'TP'})
                    position = None
        
        # Entry logic
        if position is None and sig.signal.value in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
            if sig.confidence >= 60:
                risk_amount = capital * 0.02  # 2% risk
                risk_per_unit = abs(sig.entry_price - sig.stop_loss)
                if risk_per_unit > 0:
                    size = risk_amount / risk_per_unit
                    side = 'long' if 'BUY' in sig.signal.value else 'short'
                    position = {
                        'side': side,
                        'entry': sig.entry_price,
                        'stop_loss': sig.stop_loss,
                        'take_profit': sig.take_profit,
                        'size': size,
                        'date': window.index[-1]
                    }
    except Exception as e:
        logger.debug(f"Signal error at bar {i}: {e}")
        continue

# Close any open position at last price
if position is not None:
    last_price = float(data['close'].iloc[-1])
    if position['side'] == 'long':
        pnl = (last_price - position['entry']) * position['size']
    else:
        pnl = (position['entry'] - last_price) * position['size']
    capital += pnl
    trades.append({'pnl': pnl, 'reason': 'Close'})

# Report
total_trades = len(trades)
wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] <= 0]

print(f"\n  Hasil:")
print(f"  {'─' * 40}")
print(f"  Modal Awal:     ${INITIAL_CAPITAL:>12,.2f}")
print(f"  Modal Akhir:    ${capital:>12,.2f}")
print(f"  Total Return:   {((capital/INITIAL_CAPITAL - 1) * 100):>11.2f}%")
print(f"  Total Trades:   {total_trades:>12}")
print(f"  Win Rate:       {(len(wins)/total_trades*100 if total_trades > 0 else 0):>11.1f}%")
print(f"  Avg Win:        ${(sum(t['pnl'] for t in wins)/len(wins) if wins else 0):>12,.2f}")
print(f"  Avg Loss:       ${(sum(t['pnl'] for t in losses)/len(losses) if losses else 0):>12,.2f}")
print(f"  {'─' * 40}")
```

def main():
print(”=” * 60)
print(”  GANN QUANT AI — BTCUSD Signal Generator”)
print(”=” * 60)
print(f”  Symbol:     {SYMBOL}”)
print(f”  Timeframe:  {TIMEFRAME}”)
print(f”  Period:     {START_DATE} → {END_DATE or ‘today’}”)
print(f”  Backtest:   {‘Ya’ if RUN_BACKTEST else ‘Tidak’}”)
print(”=” * 60)

```
# ─── STEP 1: Load Data ───
logger.info("Step 1: Loading data historis...")
data = load_data_with_fallback(SYMBOL, TIMEFRAME, START_DATE, END_DATE)

if data is None or data.empty:
    logger.error("Gagal load data. Abort.")
    return

logger.success(f"Data loaded: {len(data)} bars, "
               f"{data.index[0].date()} → {data.index[-1].date()}")
print(f"\n  Harga terakhir: ${data['close'].iloc[-1]:,.2f}")
print(f"  Range:          ${data['low'].min():,.2f} — ${data['high'].max():,.2f}")

# ─── STEP 2: Generate Signal ───
logger.info("\nStep 2: Generating signal untuk bar terakhir...")

try:
    signal = asyncio.run(generate_signal(data, SYMBOL, TIMEFRAME))
    print_signal_report(signal)
except Exception as e:
    logger.error(f"Signal generation error: {e}")
    import traceback
    traceback.print_exc()
    return

# ─── STEP 3: Optional Backtest ───
if RUN_BACKTEST:
    logger.info("\nStep 3: Running simple backtest...")
    try:
        run_simple_backtest(data)
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 60}")
print(f"  Selesai. Signal di atas berdasarkan bar terakhir dataset.")
print(f"  Untuk live signal, ubah END_DATE = None")
print(f"{'=' * 60}")
```

if **name** == “**main**”:
main()