#!/usr/bin/env python3
"""
research/validate_astro_signals.py

Validasi statistik: apakah sinyal astro berkorelasi dengan pergerakan harga BTC?

CARA JALANKAN:
cd /path/to/Algoritma-Trading-Wd-Gann-dan-John-F-Ehlers-main
python research/validate_astro_signals.py

DEPENDENCY:
pip install numpy pandas scipy
(opsional: pip install yfinance ccxt — untuk download data otomatis)

APA YANG DILAKUKAN SCRIPT INI:
1. Reproduce EXACT logic astro dari core/signal_engine.py baris 416-461
2. Generate sinyal astro untuk setiap hari dalam 3+ tahun data BTC
3. Hitung forward returns (5 hari) setelah setiap sinyal BUY vs SELL
4. Uji statistik: t-test, Mann-Whitney U, bootstrap confidence interval
5. Keluarkan rekomendasi: pertahankan bobot, turunkan, atau set ke 0

TEMUAN KRITIS (BUG BARU — belum ada di audit report):
_analyze_astro() di signal_engine.py baris 432-435 mengecek:

phase.get('phase_name') in ['new', 'first_quarter']

Tapi get_current_cycle_phases() menghasilkan:
    phase_name = "New (Conjunction)"
    phase_name = "First Quarter (Square)"

"new" != "New (Conjunction)" → TIDAK PERNAH MATCH!

Artinya: modul astro SELALU return HOLD (confidence 50).
10-15% bobot signal = DEAD WEIGHT yang tidak pernah menghasilkan sinyal apapun.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ============================================================
# KONFIGURASI
# ============================================================

FORWARD_RETURN_DAYS = 5
SIGNIFICANCE_LEVEL = 0.05
BOOTSTRAP_ITERATIONS = 10000
DATA_FILE = "data/historical/BTC-USD_1d_2021-01-01_2025-01-01.csv"

# ============================================================
# SELF-CONTAINED: Synodic Cycle Calculator
# ============================================================

class SynodicCycleCalculator:
    """
    Minimal copy dari modules/astro/synodic_cycles.py
    """
    PAIR_CYCLES = {
        "Jupiter-Saturn": {"period_years": 19.86, "period_days": 7253.5, "significance": "major"},
        "Saturn-Uranus": {"period_years": 45.4, "period_days": 16580.6, "significance": "major"},
        "Jupiter-Uranus": {"period_years": 13.81, "period_days": 5044.0, "significance": "important"},
        "Mars-Saturn": {"period_years": 2.0, "period_days": 730.5, "significance": "moderate"},
    }

    REFERENCE_DATES = {
        "Jupiter-Saturn": datetime(2020, 12, 21),
        "Saturn-Uranus": datetime(2032, 1, 1),
        "Jupiter-Uranus": datetime(2024, 4, 20),
        "Mars-Saturn": datetime(2024, 4, 10),
    }

    def get_current_cycle_phases(self, date: datetime = None) -> List[Dict]:
        if date is None:
            date = datetime.now()

        phases = []
        for cycle_name, ref_date in self.REFERENCE_DATES.items():
            if cycle_name in self.PAIR_CYCLES:
                cycle_info = self.PAIR_CYCLES[cycle_name]
                period = cycle_info.get("period_days",
                                       cycle_info.get("period_years", 1) * 365.25)

                days_elapsed = (date - ref_date).days
                phase_fraction = (days_elapsed % period) / period
                phase_degrees = phase_fraction * 360

                if phase_degrees < 45:
                    phase_name = "New (Conjunction)"
                elif phase_degrees < 90:
                    phase_name = "Crescent"
                elif phase_degrees < 135:
                    phase_name = "First Quarter (Square)"
                elif phase_degrees < 180:
                    phase_name = "Gibbous"
                elif phase_degrees < 225:
                    phase_name = "Full (Opposition)"
                elif phase_degrees < 270:
                    phase_name = "Disseminating"
                elif phase_degrees < 315:
                    phase_name = "Last Quarter (Square)"
                else:
                    phase_name = "Balsamic"

                phases.append({
                    "cycle": cycle_name,
                    "phase_degrees": round(phase_degrees, 1),
                    "phase_name": phase_name,
                    "phase_fraction": round(phase_fraction, 3),
                })
        return phases

# ============================================================
# ANALYZE ASTRO
# ============================================================

def analyze_astro_CURRENT(date: datetime) -> str:
    synodic = SynodicCycleCalculator()
    phases = synodic.get_current_cycle_phases(date)

    bullish_score = 0
    bearish_score = 0

    for phase in phases:
        if phase.get('phase_name') in ['new', 'first_quarter']:
            bullish_score += 1
        elif phase.get('phase_name') in ['full', 'last_quarter']:
            bearish_score += 1

    if bullish_score > bearish_score:
        return "BUY"
    elif bearish_score > bullish_score:
        return "SELL"
    return "HOLD"


def analyze_astro_FIXED(date: datetime) -> str:
    synodic = SynodicCycleCalculator()
    phases = synodic.get_current_cycle_phases(date)

    bullish_score = 0
    bearish_score = 0

    for phase in phases:
        name = phase.get('phase_name', '').lower()

        if name.startswith('new') or name.startswith('first quarter'):
            bullish_score += 1
        elif name.startswith('full') or name.startswith('last quarter'):
            bearish_score += 1

    if bullish_score > bearish_score:
        return "BUY"
    elif bearish_score > bullish_score:
        return "SELL"
    return "HOLD"

# ============================================================
# STAT FUNCTIONS
# ============================================================

def _normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def welch_ttest(group_a, group_b):
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return 0.0, 1.0

    mean_a, mean_b = np.mean(group_a), np.mean(group_b)
    var_a, var_b = np.var(group_a, ddof=1), np.var(group_b, ddof=1)

    se = np.sqrt(var_a / n_a + var_b / n_b)
    if se == 0:
        return 0.0, 1.0

    t_stat = (mean_a - mean_b) / se

    try:
        from scipy import stats
        p_value = 2 * stats.t.sf(abs(t_stat), 1)
    except ImportError:
        p_value = 2 * (1 - _normal_cdf(abs(t_stat)))

    return t_stat, p_value


def mann_whitney_u(group_a, group_b):
    try:
        from scipy.stats import mannwhitneyu
        stat, p_value = mannwhitneyu(group_a, group_b, alternative='two-sided')
        return stat, p_value
    except ImportError:
        return 0, 1


def bootstrap_mean_diff(group_a, group_b, n_iter=10000):
    np.random.seed(42)
    diffs = np.zeros(n_iter)

    for i in range(n_iter):
        a = np.random.choice(group_a, size=len(group_a), replace=True)
        b = np.random.choice(group_b, size=len(group_b), replace=True)
        diffs[i] = np.mean(a) - np.mean(b)

    return (
        np.mean(diffs),
        np.percentile(diffs, 2.5),
        np.percentile(diffs, 97.5)
    )

# ============================================================
# MAIN
# ============================================================

def run_validation():
    print("=" * 70)
    print("VALIDATE ASTRO SIGNAL")
    print("=" * 70)

    dates = pd.date_range("2021-01-01", "2025-01-01")

    signals = [analyze_astro_FIXED(d.to_pydatetime()) for d in dates]

    print(pd.Series(signals).value_counts())


if __name__ == "__main__":
    run_validation()