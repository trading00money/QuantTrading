"""
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
    'AstroEphemeris',
    'find_planetary_aspects',
    'RetrogradeCycles',
    'ZodiacDegrees',
    'SynodicCycleCalculator',
    'calculate_synodic_cycles',
    'TimeHarmonicsCalculator',
    'calculate_time_harmonics',
    'SKYFIELD_AVAILABLE',
]
