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

    assert signal == SignalType.HOLD

def test_majority_buy():
    engine = AISignalEngine()

    components = [
        DummyComponent(SignalType.BUY),
        DummyComponent(SignalType.STRONG_BUY),
        DummyComponent(SignalType.BUY),
        DummyComponent(SignalType.SELL),
    ]

    signal, _, _ = engine._combine_signals(components)

    assert signal in [SignalType.BUY, SignalType.STRONG_BUY]

def test_weak_consensus_hold():
    engine = AISignalEngine()

    components = [
        DummyComponent(SignalType.BUY),
        DummyComponent(SignalType.SELL),
        DummyComponent(SignalType.HOLD),
        DummyComponent(SignalType.SELL),
    ]

    signal, _, _ = engine._combine_signals(components)

    assert signal == SignalType.HOLD


def test_confidence_weighting():
    engine = AISignalEngine()

    components = [
        DummyComponent(SignalType.BUY, confidence=90),
        DummyComponent(SignalType.SELL, confidence=40),
        DummyComponent(SignalType.BUY, confidence=85),
    ]

    signal, _, _ = engine._combine_signals(components)

    assert signal in [SignalType.BUY, SignalType.STRONG_BUY]