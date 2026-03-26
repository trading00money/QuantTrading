import pytest
from core.execution_engine import ExecutionEngine, OrderStatus

@pytest.mark.no_mock
def test_cannot_bypass_with_manual_quantity():
    engine = ExecutionEngine(config={})

    # aktifkan kill switch
    engine.risk_gateway.risk_engine.kill_switch_active = True

    order = engine.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=999999  # bypass attempt
    )

    result = engine.submit_order(order)

    assert result.status == OrderStatus.REJECTED

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