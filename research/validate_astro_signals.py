import pandas as pd
from scipy import stats
from modules.astro.synodic_cycles import SynodicCycleCalculator


def validate_astro_correlation(price_data, significance=0.05):
    """Test apakah astro signals berkorelasi dengan returns."""

    synodic = SynodicCycleCalculator()

    # TODO: generate astro signals untuk setiap bar
    # TODO: hitung returns 5-hari setelah setiap signal

    bullish_returns = []   # Returns setelah sinyal bullish
    random_returns = []    # Returns random (baseline)

    # Safety check (hindari crash)
    if len(bullish_returns) == 0 or len(random_returns) == 0:
        print("Data tidak cukup untuk uji statistik")
        return False

    t_stat, p_value = stats.ttest_ind(bullish_returns, random_returns)

    if p_value > significance:
        print(f"Astro TIDAK signifikan (p={p_value:.4f})")
        print("REKOMENDASI: set astro weight ke 0")
        return False
    else:
        print(f"Astro signifikan (p={p_value:.4f})")
        return True