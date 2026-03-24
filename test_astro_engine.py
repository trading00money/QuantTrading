import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Tambahkan root project ke path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
# IMPORT engine kamu
from core.signal_engine import AISignalEngine

def generate_dummy_data():
    dates = pd.date_range("2021-01-01", "2026-01-01")

    price = 100
    prices = []

    for i in range(len(dates)):
        price += np.random.randn() * 0.5  # random walk
        prices.append(price)

    df = pd.DataFrame({
        'close': prices
    }, index=dates)

    return df

async def run_test():
    engine = AISignalEngine()

    data = generate_dummy_data()

    results = {
        "BUY": 0,
        "SELL": 0,
        "HOLD": 0
    }

    scores = []

    for i in range(100, len(data)):
        sub_data = data.iloc[:i]

        res = await engine._analyze_astro(sub_data, "TEST")

        if res:
            results[res.signal.name] += 1
            scores.append(res.details.get('composite_score', 0))

    print("\n=== SIGNAL DISTRIBUTION ===")
    print(results)

    print("\n=== SCORE STATS ===")
    print("Min:", min(scores))
    print("Max:", max(scores))

    print("\n=== SAMPLE OUTPUT ===")
    for i in range(5):
        print(scores[i])

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_test())