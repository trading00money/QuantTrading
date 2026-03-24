import pandas as pd
import numpy as np
import asyncio

from core.signal_engine import AISignalEngine

# =========================
# CONFIG
# =========================
INITIAL_EQUITY = 1000
HOLD_DAYS = 3
MIN_CONFIDENCE = 60
MOMENTUM_THRESHOLD = 0.1

# =========================
# DATA (dummy dulu)
# =========================
def generate_data():
    dates = pd.date_range("2021-01-01", "2024-01-01")

    price = 100
    prices = []

    for _ in range(len(dates)):
        price += np.random.randn() * 0.5
        prices.append(price)

    return pd.DataFrame({'close': prices}, index=dates)

# =========================
# BACKTEST
# =========================
async def run_backtest():
    engine = AISignalEngine()
    data = generate_data()

    equity = INITIAL_EQUITY
    trades = []
    equity_curve = []

    for i in range(100, len(data) - HOLD_DAYS):

        sub_data = data.iloc[:i]

        result = await engine._analyze_astro(sub_data, "TEST")
        if result is None:
            continue

        signal = result.signal.name
        confidence = result.confidence

        # =========================
        # FILTER 1: Confidence
        # =========================
        if confidence < MIN_CONFIDENCE:
            continue

        price_now = data['close'].iloc[i]
        price_prev = data['close'].iloc[i - 1]
        price_exit = data['close'].iloc[i + HOLD_DAYS]

        # =========================
        # FILTER 2: Momentum
        # =========================
        momentum = price_now - price_prev

        pnl = 0
        trade_taken = False

        if signal == "BUY" and momentum > MOMENTUM_THRESHOLD:
            pnl = price_exit - price_now
            trade_taken = True

        elif signal == "SELL" and momentum < -MOMENTUM_THRESHOLD:
            pnl = price_now - price_exit
            trade_taken = True

        # =========================
        # APPLY TRADE
        # =========================
        if trade_taken:
            equity += pnl
            equity_curve.append(equity)

            trades.append({
                "date": data.index[i],
                "signal": signal,
                "confidence": confidence,
                "pnl": pnl,
                "equity": equity
            })

    df = pd.DataFrame(trades)

    # =========================
    # RESULT
    # =========================
    print("\n=== BACKTEST RESULT V2 ===")
    print(f"Final Equity: {equity:.2f}")
    print(f"Total Trades: {len(df)}")

    if len(df) > 0:
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]

        winrate = len(wins) / len(df) * 100

        print(f"Winrate: {winrate:.2f}%")
        print(f"Avg Win: {wins['pnl'].mean():.4f}")
        print(f"Avg Loss: {losses['pnl'].mean():.4f}")

        print(f"Max Win: {df['pnl'].max():.4f}")
        print(f"Max Loss: {df['pnl'].min():.4f}")

        returns = df['pnl']
        sharpe = returns.mean() / returns.std() if returns.std() != 0 else 0

        print(f"Sharpe: {sharpe:.4f}")

    else:
        print("No trades executed")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(run_backtest())