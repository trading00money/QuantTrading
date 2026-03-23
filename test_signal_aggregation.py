#!/usr/bin/env python3
"""
test_signal_aggregation.py
Unit test untuk logic agregasi signal (F-04 dari Audit Report).
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ============================================================
# ENUM & DATA STRUCTURE
# ============================================================

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class SignalComponent:
    """Individual signal component from a specific engine."""
    source: str
    signal: SignalType
    confidence: float
    weight: float
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


# ============================================================
# CURRENT VERSION (BUGGY)
# ============================================================

def combine_signals_current(components: List[SignalComponent]) -> Tuple[SignalType, float, SignalStrength]:

    valid_components = [c for c in components if c.error is None and c.weight > 0]

    if not valid_components:
        return SignalType.HOLD, 50.0, SignalStrength.WEAK

    buy_score = 0
    sell_score = 0
    total_weight = 0

    for comp in valid_components:
        weight = comp.weight * (comp.confidence / 100)
        total_weight += comp.weight

        if comp.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            buy_score += weight
        elif comp.signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            sell_score += weight

    if total_weight > 0:
        buy_score /= total_weight
        sell_score /= total_weight

    if buy_score > sell_score and buy_score > 0.4:
        signal = SignalType.STRONG_BUY if buy_score > 0.7 else SignalType.BUY
        confidence = buy_score * 100
    elif sell_score > buy_score and sell_score > 0.4:
        signal = SignalType.STRONG_SELL if sell_score > 0.7 else SignalType.SELL
        confidence = sell_score * 100
    else:
        signal = SignalType.HOLD
        confidence = 50

    if confidence >= 80:
        strength = SignalStrength.VERY_STRONG
    elif confidence >= 65:
        strength = SignalStrength.STRONG
    elif confidence >= 50:
        strength = SignalStrength.MODERATE
    else:
        strength = SignalStrength.WEAK

    return signal, min(95, confidence), strength


# ============================================================
# FIXED VERSION
# ============================================================

def apply_disagreement_penalty(components: List[SignalComponent]) -> float:

    valid = [c for c in components if c.error is None and c.weight > 0]
    if len(valid) < 2:
        return 1.0

    buy_count = sum(1 for c in valid if c.signal in [SignalType.BUY, SignalType.STRONG_BUY])
    sell_count = sum(1 for c in valid if c.signal in [SignalType.SELL, SignalType.STRONG_SELL])

    min_consensus = max(2, (len(valid) + 1) // 2)
    majority = max(buy_count, sell_count)

    if buy_count >= 2 and sell_count >= 2:
        return 0.5

    if majority < min_consensus:
        return 0.7

    return 1.0


def combine_signals_fixed(components: List[SignalComponent]) -> Tuple[SignalType, float, SignalStrength]:

    valid_components = [c for c in components if c.error is None and c.weight > 0]

    if not valid_components:
        return SignalType.HOLD, 50.0, SignalStrength.WEAK

    buy_score = 0
    sell_score = 0
    total_weight = 0

    for comp in valid_components:
        weight = comp.weight * (comp.confidence / 100)
        total_weight += comp.weight

        if comp.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            buy_score += weight
        elif comp.signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            sell_score += weight

    if total_weight > 0:
        buy_score /= total_weight
        sell_score /= total_weight

    penalty = apply_disagreement_penalty(components)
    buy_score *= penalty
    sell_score *= penalty

    if buy_score > 0.3 and sell_score > 0.3:
        ratio = min(buy_score, sell_score) / max(buy_score, sell_score)
        if ratio > 0.6:
            return SignalType.HOLD, 50.0, SignalStrength.WEAK

    if buy_score > sell_score and buy_score > 0.55:
        signal = SignalType.STRONG_BUY if buy_score > 0.7 else SignalType.BUY
        confidence = buy_score * 100
    elif sell_score > buy_score and sell_score > 0.55:
        signal = SignalType.STRONG_SELL if sell_score > 0.7 else SignalType.SELL
        confidence = sell_score * 100
    else:
        signal = SignalType.HOLD
        confidence = 50

    if confidence >= 80:
        strength = SignalStrength.VERY_STRONG
    elif confidence >= 65:
        strength = SignalStrength.STRONG
    elif confidence >= 50:
        strength = SignalStrength.MODERATE
    else:
        strength = SignalStrength.WEAK

    return signal, min(95, confidence), strength


# ============================================================
# HELPER
# ============================================================

def make_component(source, signal, confidence, weight, error=None):
    return SignalComponent(
        source=source,
        signal=signal,
        confidence=confidence,
        weight=weight,
        details={"reason": f"{source} test"},
        error=error,
    )


# ============================================================
# TEST CLASS FIX
# ============================================================

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def check(self, name, actual, expected):
        ok = actual == expected
        if ok:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"

        print(f"{status}: {name} → expected={expected.value}, got={actual.value}")


# ============================================================
# SIMPLE TEST (CORE BUG)
# ============================================================

def run_test():
    components = [
        make_component('gann', SignalType.BUY, 85, 0.25),
        make_component('ml', SignalType.BUY, 85, 0.25),
        make_component('ehlers', SignalType.SELL, 85, 0.20),
        make_component('astro', SignalType.SELL, 85, 0.15),
    ]

    print("\nCURRENT:")
    print(combine_signals_current(components))

    print("\nFIXED:")
    print(combine_signals_fixed(components))


# ============================================================
# ENTRY POINT FIX
# ============================================================

if __name__ == "__main__":
    run_test()