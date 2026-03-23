import pandas as pd
from scipy import stats
from modules.astro.synodic_cycles import SynodicCycleCalculator
from download_historical_data import load_historical_data


# ============================================================
# ASTRO SIGNAL GENERATOR (STANDALONE)
# ============================================================

class AstroSignalGenerator:
    """
    Standalone astro signal generator (tanpa ubah module utama)
    """

    def __init__(self):
        self.synodic = SynodicCycleCalculator()

    def generate(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signal:
        1 = BUY
        -1 = SELL
        0 = HOLD
        """

        df = df.copy()

        base_date = df.index[0]

        # Ambil cluster dari module astro
        clusters = self.synodic.calculate_time_clusters(
            base_date, days_forward=len(df)
        )

        clusters.set_index("date", inplace=True)
        clusters = clusters.reindex(df.index, method="nearest")

        signal = pd.Series(0, index=df.index)

        strong_cluster = clusters["normalized_score"] > 40

        for i in range(2, len(df) - 2):

            if strong_cluster.iloc[i]:

                # Local bottom → BUY
                if df['close'].iloc[i] < df['close'].iloc[i - 1] and df['close'].iloc[i] < df['close'].iloc[i + 1]:
                    signal.iloc[i] = 1

                # Local top → SELL
                elif df['close'].iloc[i] > df['close'].iloc[i - 1] and df['close'].iloc[i] > df['close'].iloc[i + 1]:
                    signal.iloc[i] = -1

        return signal


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate_astro_correlation(price_data, significance=0.05):

    astro = AstroSignalGenerator()

    # Generate astro signal
    price_data['astro_signal'] = astro.generate(price_data)

    print("\nDistribusi Signal:")
    print(price_data['astro_signal'].value_counts())

    # Return masa depan (5 hari)
    price_data['return_5d'] = price_data['close'].pct_change(5).shift(-5)

    # Ambil hanya BUY signal
    bullish_returns = price_data.loc[
        price_data['astro_signal'] == 1,
        'return_5d'
    ].dropna()

    if len(bullish_returns) < 30:
        print("\n❌ Sample terlalu kecil")
        return False

    # Baseline random
    random_returns = price_data['return_5d'].dropna().sample(len(bullish_returns))

    # Statistical test (Welch t-test)
    t_stat, p_value = stats.ttest_ind(
        bullish_returns,
        random_returns,
        equal_var=False
    )

    # Metrics tambahan
    mean_return = bullish_returns.mean()
    winrate = (bullish_returns > 0).mean()

    print("\n===== HASIL VALIDASI ASTRO =====")
    print(f"Sample: {len(bullish_returns)}")
    print(f"Mean return: {mean_return:.5f}")
    print(f"Winrate: {winrate:.2%}")
    print(f"p-value: {p_value:.4f}")

    # Keputusan
    if p_value > significance or mean_return <= 0:
        print("\n❌ Astro TIDAK signifikan → REKOMENDASI: weight = 0")
        return False
    else:
        print("\n✅ Astro signifikan → bisa dipakai (weight kecil dulu)")
        return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("========================================")
    print(" VALIDATE ASTRO SIGNAL")
    print("========================================")

    df = load_historical_data("BTC-USD", "1d", "2021-01-01", "2025-01-01")

    if df is None:
        print("❌ Data tidak ditemukan. Jalankan downloader dulu.")
    else:
        validate_astro_correlation(df)