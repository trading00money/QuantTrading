# core/feature_builder.py

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, List, Optional


class FeatureBuilder:

    def __init__(self, config: Dict):
        self.config = config
        self.ml_config = config.get("ml_config", {}).get("feature_engineering", {})
        logger.info("FeatureBuilder initialized.")

    def build_features(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict[str, List[float]]],
        astro_events: Optional[pd.DataFrame],
        mode: str = "prediction"   # 🔥 DEFAULT: TANPA TARGET
    ) -> pd.DataFrame:

        assert mode in ["training", "prediction"]

        logger.info("Building features for ML model...")

        if price_data is None:
            logger.error("price_data is None")
            return None

        # 🔥 DEEP COPY (WAJIB)
        features = price_data.copy(deep=True)

        # =========================
        # 1. RETURNS
        # =========================
        for n in [5, 10, 20, 60]:
            features[f'return_{n}d'] = features['close'].pct_change(n)

        # =========================
        # 2. RSI
        # =========================
        features['rsi'] = self._calculate_rsi(features['close'])

        # =========================
        # 3. FISHER (SAFE CHECK)
        # =========================
        if 'fisher' not in features.columns:
            features['fisher'] = 0

        # =========================
        # 4. ASTRO
        # =========================
        if astro_events is not None and not astro_events.empty:
            features['is_astro_event'] = 0
            features.loc[astro_events.index, 'is_astro_event'] = 1
        else:
            features['is_astro_event'] = 0

        # =========================
        # ❌ TIDAK ADA TARGET DI SINI
        # =========================

        # =========================
        # SELECT FEATURES
        # =========================
        feature_cols = [
            'return_5d', 'return_10d', 'return_20d', 'return_60d',
            'rsi', 'fisher',
            'is_astro_event'
        ]

        features = features[[c for c in feature_cols if c in features.columns]]

        # 🔥 DROP NA
        features = features.dropna()

        # 🔥 REMOVE RETURN (AGAR TIDAK TERLALU KUAT)
        features = features.drop(columns=[
            'return_5d', 'return_10d', 'return_20d', 'return_60d'
        ], errors='ignore')

        # 🔥 REMOVE RAW PRICE
        features = features.drop(columns=[
            'open', 'high', 'low', 'close',
            'tick_volume', 'real_volume', 'spread'
        ], errors='ignore')

        print("FEATURE SAMPLE:")
        print(features.head())

        logger.success(f"Feature building complete. Shape: {features.shape}")

        return features

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))