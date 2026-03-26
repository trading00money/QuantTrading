import pandas as pd
from core.signal_engine import run_async_signal

# === LOAD DATA ===
data = pd.read_csv("data.csv")  # pakai data OHLC kamu
data.columns = [c.lower() for c in data.columns]

# pastikan ada: open, high, low, close
data = data.tail(300)  # ambil 300 candle terakhir

# === BACKTEST FUNCTION ===
def run_backtest(data, use_dynamic=True):
    balance = 10000
    risk_per_trade = 0.01

    wins = 0
    losses = 0
    total_profit = 0

    for i in range(50, len(data)):
        df = data.iloc[:i]

        signal = run_async_signal(
            symbol="TEST",
            data=df,
            timeframe="H1"
        )

        # 🔴 skip HOLD
        if signal.signal.value == "HOLD":
            continue

        entry = signal.entry_price

        # === override mode ===
        if not use_dynamic:
            atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
            sl = entry - (atr * 1.5) if signal.signal.value == "BUY" else entry + (atr * 1.5)
            tp = entry + (atr * 3) if signal.signal.value == "BUY" else entry - (atr * 3)
        else:
            sl = signal.stop_loss
            tp = signal.take_profit

        # simulate next candle
        next_candle = data.iloc[i]

        hit_sl = False
        hit_tp = False

        if signal.signal.value == "BUY":
            if next_candle['low'] <= sl:
                hit_sl = True
            elif next_candle['high'] >= tp:
                hit_tp = True
        else:
            if next_candle['high'] >= sl:
                hit_sl = True
            elif next_candle['low'] <= tp:
                hit_tp = True

        risk = abs(entry - sl)
        reward = abs(tp - entry)

        if hit_tp:
            profit = reward
            wins += 1
        elif hit_sl:
            profit = -risk
            losses += 1
        else:
            continue

        total_profit += profit

    total_trades = wins + losses
    winrate = wins / total_trades if total_trades > 0 else 0

    return {
        "profit": total_profit,
        "trades": total_trades,
        "winrate": round(winrate * 100, 2)
    }


# === RUN TEST ===
fixed = run_backtest(data, use_dynamic=False)
dynamic = run_backtest(data, use_dynamic=True)

print("\n=== RESULT ===")
print("FIXED:", fixed)
print("DYNAMIC:", dynamic)