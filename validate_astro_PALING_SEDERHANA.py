#!/usr/bin/env python3
"""
VALIDATE ASTRO — VERSI PALING SEDERHANA
Tidak import apapun dari project.
Tidak butuh library apapun.
Hanya butuh Python.

CARA PAKAI:
  python validate_astro_PALING_SEDERHANA.py
"""

import math
from datetime import datetime, timedelta

REF = datetime(2024, 4, 10)
PERIOD = 730.5

start = datetime(2021, 1, 1)
end = datetime(2025, 1, 1)

buy = 0
hold = 0
sell = 0
total = 0

current = start
while current <= end:
    days = (current - REF).days
    deg = ((days % PERIOD) / PERIOD) * 360
    score = math.cos(math.radians(deg))

    if score > 0.3:
        buy += 1
    elif score < -0.3:
        sell += 1
    else:
        hold += 1

    total += 1
    current += timedelta(days=1)

print(f"BUY:  {buy} ({buy/total*100:.1f}%)")
print(f"HOLD: {hold} ({hold/total*100:.1f}%)")
print(f"SELL: {sell} ({sell/total*100:.1f}%)")
print(f"Total: {total}")
