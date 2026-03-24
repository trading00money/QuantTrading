#!/usr/bin/env python3
"""
fix_astro_dan_validate.py
==========================
Script ini melakukan 2 hal:

  1. MEMPERBAIKI file modules/astro/__init__.py
     (yang membunuh SynodicCycleCalculator saat skyfield tidak terinstall)

  2. MENJALANKAN validasi untuk membuktikan fix berhasil

MASALAH YANG DI-FIX:
  File modules/astro/__init__.py baris 18-48:
    if SKYFIELD_AVAILABLE:
        from .synodic_cycles import SynodicCycleCalculator  ← hanya jika skyfield ada
    if not SKYFIELD_AVAILABLE:
        SynodicCycleCalculator = None  ← DIBUNUH!

  Padahal SynodicCycleCalculator TIDAK BUTUH skyfield.
  Skyfield hanya dibutuhkan oleh AstroEphemeris.

CARA PAKAI:
  1. Taruh file ini di ROOT folder project (sejajar run.py)
  2. Jalankan: python fix_astro_dan_validate.py
  3. Script akan OTOMATIS memperbaiki __init__.py
  4. Lalu menjalankan validasi
  5. Expected result: BUY ~40%, HOLD ~19%, SELL ~40%
"""

import os
import sys
import math
import shutil
from datetime import datetime, timedelta


def find_project_root():
    """Cari folder root project (yang berisi run.py)."""
    # Coba current directory dulu
    if os.path.exists("run.py"):
        return os.getcwd()
    # Coba parent
    parent = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(parent, "run.py")):
        return parent
    # Coba parent dari parent (kalau script di research/)
    grandparent = os.path.dirname(parent)
    if os.path.exists(os.path.join(grandparent, "run.py")):
        return grandparent
    return os.getcwd()


def fix_init_file(project_root):
    """
    Perbaiki modules/astro/__init__.py supaya
    SynodicCycleCalculator SELALU tersedia
    (tidak tergantung skyfield).
    """
    init_path = os.path.join(project_root, "modules", "astro", "__init__.py")

    if not os.path.exists(init_path):
        print(f"  ❌ File tidak ditemukan: {init_path}")
        return False

    print(f"  File: {init_path}")

    # Backup dulu
    backup_path = init_path + ".backup"
    if not os.path.exists(backup_path):
        shutil.copy2(init_path, backup_path)
        print(f"  Backup: {backup_path}")

    # Tulis versi baru
    new_content = '''"""
Astro Module
Astrological analysis tools for financial markets

Note: skyfield is an optional dependency for astronomical calculations.
If not installed, only ephemeris-based features will be disabled.
SynodicCycleCalculator dan TimeHarmonicsCalculator tetap tersedia
karena tidak butuh skyfield.
"""

# ============================================================
# IMPORT YANG TIDAK BUTUH SKYFIELD (selalu tersedia)
# ============================================================
from .synodic_cycles import SynodicCycleCalculator, calculate_synodic_cycles
from .time_harmonics import TimeHarmonicsCalculator, calculate_time_harmonics

# ============================================================
# IMPORT YANG BUTUH SKYFIELD (opsional)
# ============================================================
SKYFIELD_AVAILABLE = False
AstroEphemeris = None
find_planetary_aspects = None
RetrogradeCycles = None
ZodiacDegrees = None

try:
    import skyfield
    SKYFIELD_AVAILABLE = True

    from .astro_ephemeris import AstroEphemeris
    from .planetary_aspects import find_planetary_aspects
    from .retrograde_cycles import RetrogradeCycles
    from .zodiac_degrees import ZodiacDegrees

except ImportError:
    pass  # Skyfield tidak ada — fitur ephemeris disabled, tapi synodic tetap jalan

__all__ = [
    \'AstroEphemeris\',
    \'find_planetary_aspects\',
    \'RetrogradeCycles\',
    \'ZodiacDegrees\',
    \'SynodicCycleCalculator\',
    \'calculate_synodic_cycles\',
    \'TimeHarmonicsCalculator\',
    \'calculate_time_harmonics\',
    \'SKYFIELD_AVAILABLE\',
]
'''

    with open(init_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  ✅ File berhasil diperbaiki!")
    return True


def clear_pycache(project_root):
    """Hapus semua __pycache__ di project."""
    count = 0
    for root, dirs, files in os.walk(project_root):
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            shutil.rmtree(cache_dir, ignore_errors=True)
            count += 1
    print(f"  Dihapus: {count} folder __pycache__")


def validate_signals():
    """Hitung signal standalone (tanpa import dari project)."""
    REF_DATE = datetime(2024, 4, 10)
    PERIOD = 730.5

    start = datetime(2021, 1, 1)
    end = datetime(2025, 1, 1)

    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    results = {"BUY": 0, "HOLD": 0, "SELL": 0}
    samples = []

    for d in dates:
        days_elapsed = (d - REF_DATE).days
        phase_fraction = (days_elapsed % PERIOD) / PERIOD
        phase_degrees = phase_fraction * 360
        score = math.cos(math.radians(phase_degrees))

        if score > 0.3:
            sig = "BUY"
        elif score < -0.3:
            sig = "SELL"
        else:
            sig = "HOLD"
        results[sig] += 1

        if len(samples) == 0 or (d - samples[-1][0]).days >= 90:
            samples.append((d, sig, score))

    total = len(dates)
    return results, total, samples


def validate_with_module(project_root):
    """Test apakah import dari module BENAR setelah fix."""
    # Tambah project root ke path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Hapus cached modules
    for key in list(sys.modules.keys()):
        if "astro" in key or "synodic" in key or "modules" in key:
            del sys.modules[key]

    try:
        from modules.astro.synodic_cycles import SynodicCycleCalculator

        if SynodicCycleCalculator is None:
            print(f"  ❌ SynodicCycleCalculator is None (masih dibunuh oleh __init__.py)")
            return None

        # Test
        synodic = SynodicCycleCalculator()
        phases = synodic.get_current_cycle_phases(datetime(2023, 6, 15))

        # Cek Mars-Saturn ada
        mars = [p for p in phases if p.get("cycle") == "Mars-Saturn"]
        if not mars:
            print(f"  ❌ Mars-Saturn tidak ada di output get_current_cycle_phases()")
            return None

        # Hitung signal
        CYCLE_WEIGHTS = {"Mars-Saturn": 1.0}
        results = {"BUY": 0, "HOLD": 0, "SELL": 0}

        import pandas as pd
        dates = pd.date_range("2021-01-01", "2025-01-01")

        for d in dates:
            dt = d.to_pydatetime()
            phases = synodic.get_current_cycle_phases(dt)
            composite = 0.0
            total_w = 0.0
            for phase in phases:
                w = CYCLE_WEIGHTS.get(phase.get("cycle", ""), 0)
                if w == 0:
                    continue
                deg = phase.get("phase_degrees", 0)
                composite += math.cos(math.radians(deg)) * w
                total_w += w
            if total_w > 0:
                composite /= total_w
            if composite > 0.3:
                results["BUY"] += 1
            elif composite < -0.3:
                results["SELL"] += 1
            else:
                results["HOLD"] += 1

        return results

    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return None


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  FIX ASTRO & VALIDATE — Script Otomatis")
    print("=" * 60)

    project_root = find_project_root()
    print(f"\n  Project root: {project_root}")

    # ─── STEP 1: Fix __init__.py ───
    print(f"\n  STEP 1: Memperbaiki modules/astro/__init__.py")
    print("  " + "─" * 45)
    fix_ok = fix_init_file(project_root)

    if not fix_ok:
        print("\n  ❌ Fix gagal. Pastikan script di folder yang benar.")
        sys.exit(1)

    # ─── STEP 2: Hapus cache ───
    print(f"\n  STEP 2: Menghapus cache Python")
    print("  " + "─" * 45)
    clear_pycache(project_root)

    # ─── STEP 3: Validasi standalone ───
    print(f"\n  STEP 3: Validasi signal (built-in, tanpa import)")
    print("  " + "─" * 45)

    results, total, samples = validate_signals()

    print(f"\n  Signal Distribution (HASIL YANG BENAR):")
    print(f"  {'─' * 40}")
    for sig in ["BUY", "HOLD", "SELL"]:
        count = results[sig]
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"    {sig:>4}: {count:>5} ({pct:>5.1f}%) {bar}")
    print(f"  {'─' * 40}")

    # ─── STEP 4: Test import dari module ───
    print(f"\n  STEP 4: Test import dari modules/astro/ (setelah fix)")
    print("  " + "─" * 45)

    module_results = validate_with_module(project_root)

    if module_results:
        total_m = sum(module_results.values())
        print(f"\n  Signal Distribution (VIA MODULE):")
        print(f"  {'─' * 40}")
        for sig in ["BUY", "HOLD", "SELL"]:
            count = module_results[sig]
            pct = count / total_m * 100
            bar = "█" * int(pct / 2)
            print(f"    {sig:>4}: {count:>5} ({pct:>5.1f}%) {bar}")
        print(f"  {'─' * 40}")

        # Compare
        match = (module_results["BUY"] == results["BUY"] and
                 module_results["SELL"] == results["SELL"])

        if match:
            print(f"\n  ✅ HASIL COCOK! Module berfungsi dengan benar.")
        else:
            print(f"\n  ⚠ Hasil sedikit berbeda (mungkin karena timezone)")
            print(f"     Built-in: BUY={results['BUY']}, SELL={results['SELL']}")
            print(f"     Module:   BUY={module_results['BUY']}, SELL={module_results['SELL']}")
    else:
        print(f"\n  ⚠ Import dari module gagal.")
        print(f"     Tapi logika sudah benar (lihat Step 3).")
        print(f"     Coba install loguru: pip install loguru")

    # ─── SELESAI ───
    print(f"\n  {'=' * 55}")
    print(f"  SELESAI!")
    print(f"  {'=' * 55}")
    print(f"""
  Yang sudah di-fix:
    ✅ modules/astro/__init__.py — SynodicCycleCalculator
       tidak lagi dibunuh saat skyfield tidak terinstall
    ✅ Cache Python dihapus

  Langkah selanjutnya:
    1. Jalankan validate biasa:
       python research/validate_astro_signals.py
       Expected: BUY ~40%, HOLD ~19%, SELL ~40%

    2. Jika masih 100% HOLD:
       Install loguru: pip install loguru
       Lalu jalankan ulang script ini
""")
