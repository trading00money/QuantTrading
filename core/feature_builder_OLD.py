import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, List, Optional

class FeatureBuilder:
    """
    Constructs a feature set for machine learning models from various data sources.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.ml_config = config.get("ml_config", {}).get("feature_engineering", {})
        logger.info("FeatureBuilder initialized.")

    def build_features(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict[str, List[float]]],
        astro_events: Optional[pd.DataFrame],
        mode: str = "training"
    ) -> pd.DataFrame:
        """
        Creates a comprehensive feature DataFrame for the ML model.

        Args:
            price_data (pd.DataFrame): DataFrame with OHLCV and other indicators (like Ehlers).
            gann_levels (Optional[Dict[str, List[float]]]): Gann support/resistance levels.
            astro_events (Optional[pd.DataFrame]): DataFrame of astrological events.

        Returns:
            pd.DataFrame: A DataFrame with features and a target variable.
        """
        assert mode in ["training", "prediction"], "mode harus 'training' atau 'prediction'"
        logger.info("Building features for ML model...")
        if price_data is None:
            logger.error("price_data is None — cannot build features")
            return None

        features = price_data.copy()
        # 🔥 PUTUS RELASI DENGAN SOURCE
        features = features.copy(deep=True)



        # 1. Price-based features
        for n in [5, 10, 20, 60]:
            features[f'return_{n}d'] = features['close'].pct_change(n)
        features['rsi'] = self._calculate_rsi(features['close'])

        # 2. Ehlers features (already in the DataFrame)
        # Ensure they exist to avoid errors
        if 'fisher' not in features.columns:
            features['fisher'] = 0

        # 3. Gann features
        # if gann_levels:
        #     features['dist_to_gann_sup'] = self._dist_to_nearest_level(features['close'], gann_levels['support'])
        #     features['dist_to_gann_res'] = self._dist_to_nearest_level(features['close'], gann_levels['resistance'])
        # else:
        #     features['dist_to_gann_sup'] = np.nan
        #     features['dist_to_gann_res'] = np.nan
        # window = 100

        # rolling_low = features['low'].rolling(window).min()
        # rolling_high = features['high'].rolling(window).max()

        # features['dist_to_gann_sup'] = features['close'] - rolling_low
        # features['dist_to_gann_res'] = rolling_high - features['close']

        # 4. Astro features
        if astro_events is not None and not astro_events.empty:
            features['is_astro_event'] = 0
            features.loc[astro_events.index, 'is_astro_event'] = 1
        else:
            features['is_astro_event'] = 0

        # 5. Target variable
        target_period = self.ml_config.get("target_period", 5)

        if mode == "training":
            import numpy as np

            # Hitung future return
            future_return = (
                features['close'].shift(-target_period) - features['close']
            ) / features['close']

            # lebih ketat + lebih realistis
            features['target'] = np.where(
                future_return > 0.02, 1,      # naik 2%
                np.where(future_return < -0.02, 0, np.nan)
            )

            features = features.dropna(subset=['target'])

            # Buang tail yang tidak punya future
            features = features.iloc[:-target_period]

        elif mode == "prediction":
            # Pastikan tidak ada target
            if 'target' in features.columns:
                raise ValueError("CRITICAL: target tidak boleh ada di prediction mode!")
        
        # 6. Cleanup
        # Drop original OHLCV and select feature columns
        feature_cols = [
            'return_5d', 'return_10d', 'return_20d', 'return_60d',
            'rsi', 'fisher',
            # 'dist_to_gann_sup', 'dist_to_gann_res',
            'is_astro_event'
        ]

        # Tambahkan target hanya kalau training
        if mode == "training":
            feature_cols.append('target')

        # Keep only columns that were successfully created
        final_cols = [col for col in feature_cols if col in features.columns]
        features = features[final_cols]

        # 🔥 DEBUG: pakai hanya 1 feature
        # features = features[['rsi', 'target']]
        # features = features[['fisher', 'target']]
        # features = features[['dist_to_gann_sup', 'target']]
        features = features.dropna()
        # ❌ REMOVE FEATURE TERLALU KUAT (sementara untuk test)
        features = features.drop(columns=[
            'return_5d',
            'return_10d',
            'return_20d',
            'return_60d'
        ], errors='ignore')

        # 🔥 HAPUS SEMUA RAW PRICE
        features = features.drop(columns=[
            'open', 'high', 'low', 'close',
            'tick_volume', 'real_volume', 'spread'
        ], errors='ignore')
        
        print("FEATURE SAMPLE:")
        print(features.head())

        print("FEATURE INPUT ROWS:", len(price_data))
        print("AFTER FEATURE ENGINEERING:", len(features))
        logger.success(f"Feature building complete. Shape: {features.shape}")

        return features

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _dist_to_nearest_level(self, prices: pd.Series, levels: List[float]) -> pd.Series:
        """Calculates normalized distance to the nearest Gann level."""
        if not levels:
            return pd.Series(np.nan, index=prices.index)

        dist_matrix = pd.DataFrame({level: (prices - level) / prices for level in levels})
        return dist_matrix.abs().min(axis=1)
