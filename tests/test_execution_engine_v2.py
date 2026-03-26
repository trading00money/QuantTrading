import pytest
from core.execution_engine import ExecutionEngine, OrderStatus


# ===============================
# 🔧 HELPER: MOCK RISK GATEWAY
# ===============================
def mock_risk_gateway(engine, approved=True, size=0.01):
    class Decision:
        def __init__(self):
            self.approved = approved
            self.position_size = size
            self.reason = "mocked"
            self.risk_level = "low"

    engine.risk_gateway.evaluate_trade = lambda **kwargs: Decision()


# ===============================
# ✅ BASIC FLOW TESTS
# ===============================
def test_engine_initialization():
    engine = ExecutionEngine(config={})
    assert engine is not None


def test_create_order():
    engine = ExecutionEngine(config={})
    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    assert order.symbol == "BTCUSDT"
    assert order.quantity == 1


# ===============================
# ✅ NORMAL EXECUTION (MOCK RISK)
# ===============================
def test_paper_order_execution_buy():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    result = engine.submit_order(order)

    assert result.status == OrderStatus.FILLED


def test_paper_order_execution_sell():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    order = engine.create_order(
        symbol="BTCUSDT",
        side="SELL",
        order_type="MARKET",
        quantity=1
    )

    result = engine.submit_order(order)

    assert result.status == OrderStatus.FILLED


def test_limit_order_creation():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        price=30000
    )

    result = engine.submit_order(order)

    assert result.status in [OrderStatus.FILLED, OrderStatus.SUBMITTED]


# ===============================
# ✅ POSITION TEST
# ===============================
def test_position_tracking():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    engine.buy_market("BTCUSDT", 1)

    positions = engine.get_all_positions()

    assert len(positions) >= 1


def test_close_position():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    engine.buy_market("BTCUSDT", 1)
    result = engine.close_position("BTCUSDT")

    assert result is not None


# ===============================
# ❌ CRITICAL TEST (NO MOCK)
# ===============================
@pytest.mark.no_mock
def test_kill_switch_blocks_order():
    engine = ExecutionEngine(config={})

    # AKTIFKAN KILL SWITCH
    engine.risk_gateway.risk_engine.kill_switch_active = True

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    result = engine.submit_order(order)

    assert result.status == OrderStatus.REJECTED
    assert "KILL" in result.error_message.upper()

@pytest.mark.no_mock
def test_all_orders_blocked_when_kill_switch():
    engine = ExecutionEngine(config={})
    engine.risk_gateway.risk_engine.kill_switch_active = True

    for _ in range(10):
        order = engine.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=1
        )

        result = engine.submit_order(order)

        assert result.status == OrderStatus.REJECTED


# ===============================
# ❌ EDGE CASE TEST
# ===============================
@pytest.mark.no_mock
def test_zero_position_size_rejected():
    engine = ExecutionEngine(config={})

    class MockDecision:
        approved = True
        position_size = 0
        reason = "zero size"
        risk_level = "low"

    engine.risk_gateway.evaluate_trade = lambda **kwargs: MockDecision()

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    result = engine.submit_order(order)

    assert result.status == OrderStatus.REJECTED


def test_invalid_market_price():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    # Paksa harga invalid
    engine._get_market_price = lambda x: 0

    result = engine.submit_order(order)

    assert result.status == OrderStatus.REJECTED


# ===============================
# 🔥 STRESS TEST
# ===============================
def test_multiple_orders_stability():
    engine = ExecutionEngine(config={})
    mock_risk_gateway(engine)

    for _ in range(50):
        order = engine.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=1
        )
        result = engine.submit_order(order)
        assert result.status in [OrderStatus.FILLED, OrderStatus.SUBMITTED]


# ===============================
# 🔒 SAFETY TEST
# ===============================
def test_risk_gateway_mandatory():
    engine = ExecutionEngine(config={})

    engine.risk_gateway = None  # simulate bug

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1
    )

    with pytest.raises(Exception):
        engine.submit_order(order)