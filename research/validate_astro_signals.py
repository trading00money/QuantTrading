#!/usr/bin/env python3
"""
validate_astro_signals.py (V3 — TRULY FIXED)

MASALAH SEBELUMNYA:
    modules/astro/__init__.py mengecek apakah 'skyfield' terinstall.
    Jika TIDAK → SynodicCycleCalculator di-set ke None.
    Padahal SynodicCycleCalculator TIDAK BUTUH skyfield sama sekali!
    (Skyfield hanya dibutuhkan oleh astro_ephemeris.py, bukan synodic_cycles.py)

SOLUSI:
    Import LANGSUNG dari file, bukan lewat package __init__.py:
    from modules.astro.synodic_cycles import SynodicCycleCalculator
    ↓ berubah menjadi ↓
    Baca file langsung pakai importlib

CARA JALANKAN:
    cd /path/to/project-root
    python research/validate_astro_signals.py

EXPECTED OUTPUT:
    BUY:  589 (40.3%)
    HOLD: 284 (19.4%)
    SELL: 589 (40.3%)
"""

import math
import sys
import os
import importlib.util
import pandas as pd
from datetime import datetime

# ============================================================
# IMPORT LANGSUNG — bypass modules/astro/__init__.py
# ============================================================

def load_synodic_calculator():
    """
    Load SynodicCycleCalculator LANGSUNG dari file .py,
    tanpa lewat __init__.py yang butuh skyfield.
    """
    # Cari path ke synodic_cycles.py
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    synodic_path = os.path.join(project_root, "modules", "astro", "synodic_cycles.py")

    if not os.path.exists(synodic_path):
        print(f"  ERROR: File tidak ditemukan: {synodic_path}")
        print(f"  Pastikan script ini ada di folder research/ dalam project")
        sys.exit(1)

    # Mock loguru jika belum terinstall
    if 'loguru' not in sys.modules:
        try:
            import loguru
        except ImportError:
            import types
            mock = types.ModuleType('loguru')
            class _Logger:
                def info(self, *a, **kw): pass
                def debug(self, *a, **kw): pass
                def warning(self, *a, **kw): pass
                def success(self, *a, **kw): pass
                def error(self, *a, **kw): pass
            mock.logger = _Logger()
            sys.modules['loguru'] = mock

    # Load module langsung dari file
    spec = importlib.util.spec_from_file_location("synodic_cycles", synodic_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.SynodicCycleCalculator


# ============================================================
# ASTRO SCORING V3
# ============================================================

def analyze_astro_v3(date, SynodicClass):
    """
    V3: Hanya Mars-Saturn (cycle yang cycling penuh).

    Kenapa hanya Mars-Saturn:
    - Mars-Saturn period = 730 hari = 2 rotasi penuh dalam 4 tahun ✓
    - Jupiter-Saturn period = 7254 hari = 0.20 rotasi → BIAS PERMANEN
    - Jupiter-Uranus period = 5044 hari = 0.29 rotasi → BIAS PERMANEN
    - Saturn-Uranus period = 16581 hari = 0.09 rotasi → BIAS PERMANEN
    """
    synodic = SynodicClass()
    phases = synodic.get_current_cycle_phases(date)

    CYCLE_WEIGHTS = {'Mars-Saturn': 1.0}

    composite = 0.0
    total_w = 0.0

    for phase in phases:
        w = CYCLE_WEIGHTS.get(phase.get('cycle', ''), 0)
        if w == 0:
            continue
        deg = phase.get('phase_degrees', 0)
        composite += math.cos(math.radians(deg)) * w
        total_w += w

    if total_w > 0:
        composite /= total_w

    if composite > 0.3:
        return "BUY", composite
    elif composite < -0.3:
        return "SELL", composite
    return "HOLD", composite


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  Validate Astro Signals V3 (Mars-Saturn Only)")
    print("=" * 55)

    # Load class langsung dari file
    print("\n  Loading SynodicCycleCalculator...", end=" ")
    SynodicCycleCalculator = load_synodic_calculator()
    print("OK")

    # Generate signals untuk 4 tahun
    print("  Generating signals 2021-2025...", end=" ")
    dates = pd.date_range("2021-01-01", "2025-01-01")
    signals = []
    scores = []

    for d in dates:
        signal, score = analyze_astro_v3(d.to_pydatetime(), SynodicCycleCalculator)
        signals.append(signal)
        scores.append(score)

    print(f"Done ({len(signals)} hari)")

    # Distribusi
    counts = pd.Series(signals).value_counts()

    print("\n  Signal Distribution:")
    print(f"  {'─' * 35}")
    for signal_type in ["BUY", "HOLD", "SELL"]:
        count = counts.get(signal_type, 0)
        pct = count / len(signals) * 100
        bar = "█" * int(pct / 2)
        print(f"    {signal_type:>4}: {count:>5} ({pct:>5.1f}%) {bar}")
    print(f"  {'─' * 35}")
    print(f"    Total: {len(signals)}")

    # Balance check
    buy_count = counts.get("BUY", 0)
    sell_count = counts.get("SELL", 0)
    if buy_count > 0 and sell_count > 0:
        ratio = min(buy_count, sell_count) / max(buy_count, sell_count)
        print(f"\n    BUY/SELL ratio: {ratio:.2f}", end="")
        if ratio > 0.8:
            print(" ✅ SEIMBANG")
        elif ratio > 0.5:
            print(" ⚠ Sedikit tidak seimbang")
        else:
            print(" ❌ BIAS")
    elif buy_count == 0 and sell_count == 0:
        print("\n    ❌ SEMUA HOLD — ada masalah!")
    else:
        print(f"\n    ❌ Hanya ada {('BUY' if buy_count > 0 else 'SELL')} — tidak seimbang!")

    # Beberapa contoh
    print(f"\n  Contoh sinyal per-kuartal:")
    import numpy as np
    scores_arr = np.array(scores)
    for i in range(0, len(dates), 90):
        if i < len(dates):
            d = dates[i]
            print(f"    {d.date()}: {signals[i]:>4} (score: {scores[i]:>+.4f})")

    print(f"\n{'=' * 55}")
    print(f"  Selesai.")
    print(f"{'=' * 55}")
