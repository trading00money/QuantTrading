import pandas as pd
from scipy import stats
from modules.astro.synodic_cycles import SynodicCycleCalculator
from download_historical_data import load_historical_data

df = load_historical_data("BTC-USD", "1d", "2021-01-01", "2025-01-01")

def validate_astro_correlation(price_data, significance=0.05):

    synodic = SynodicCycleCalculator()

    # Generate astro signal
    price_data['astro_signal'] = synodic.generate_signal(price_data)

    # Return masa depan
    price_data['return_5d'] = price_data['close'].pct_change(5).shift(-5)

    # Ambil hanya saat BUY
    bullish_returns = price_data.loc[
        price_data['astro_signal'] == 1,
        'return_5d'
    ].dropna()

    if len(bullish_returns) < 30:
        print("Sample terlalu kecil")
        return False

    # Baseline random
    random_returns = price_data['return_5d'].dropna().sample(len(bullish_returns))

    # Statistical test (WAJIB pakai ini)
    t_stat, p_value = stats.ttest_ind(
        bullish_returns,
        random_returns,
        equal_var=False
    )

    # Tambahan penting
    mean_return = bullish_returns.mean()
    winrate = (bullish_returns > 0).mean()

    print(f"Sample: {len(bullish_returns)}")
    print(f"Mean return: {mean_return:.5f}")
    print(f"Winrate: {winrate:.2%}")
    print(f"p-value: {p_value:.4f}")

    if p_value > significance or mean_return <= 0:
        print("❌ Astro TIDAK signifikan → weight = 0")
        return False
    else:
        print("✅ Astro signifikan")
        return True
        
if __name__ == "__main__":
    if df is None:
        print("❌ Data gagal di-load")
    else:
        validate_astro_correlation(df)