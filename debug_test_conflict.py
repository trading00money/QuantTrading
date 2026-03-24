import pytest
from core.signal_engine import AISignalEngine, SignalType

class DummyComponent:
    def __init__(self, signal, confidence=80, weight=1.0):
        self.signal = signal
        self.confidence = confidence
        self.weight = weight
        self.error = None

def test_conflict_should_hold():
    engine = AISignalEngine()

    components = [
        DummyComponent(SignalType.BUY),
        DummyComponent(SignalType.STRONG_BUY),
        DummyComponent(SignalType.SELL),
        DummyComponent(SignalType.STRONG_SELL),
    ]

    signal, confidence, strength = engine._combine_signals(components)

    print(f"[DEBUG] penalty: {penalty}")
    print(f"[DEBUG] buy_score: {buy_score}, sell_score: {sell_score}")

    assert signal == SignalType.HOLD