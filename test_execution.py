from core.execution_engine import ExecutionEngine
config = {
    "paper_trading": {
        "initial_balance": 100000.0
    },
    "risk": {
        "max_position_size": 0.1,
        "max_daily_loss": 0.05,
        "max_open_positions": 5
    },
    "broker_config": {}
}
engine = ExecutionEngine(config=config)

def test_invalid_quantity():
    order = engine.create_order(
        symbol="XAUUSD",
        side="BUY",
        order_type="MARKET",
        quantity=-1
    )

    print("\n[TEST] Invalid Quantity")
    print("Status :", order.status)
    print("Error  :", order.error_message)


def test_invalid_sl_buy():
    order = engine.create_order(
        symbol="XAUUSD",
        side="BUY",
        order_type="LIMIT",
        price=2000,
        quantity=1,
        stop_loss=2100
    )

    print("\n[TEST] BUY SL Salah")
    print("Status :", order.status)
    print("Error  :", order.error_message)


def test_invalid_sl_sell():
    order = engine.create_order(
        symbol="XAUUSD",
        side="SELL",
        order_type="LIMIT",
        price=2000,
        quantity=1,
        stop_loss=1900
    )

    print("\n[TEST] SELL SL Salah")
    print("Status :", order.status)
    print("Error  :", order.error_message)

def test_submit_order_flow():
    order = engine.create_order(
        symbol="XAUUSD",
        side="BUY",
        order_type="MARKET",
        quantity=1,
        stop_loss=49000  # valid (di bawah market 50000)
    )

    order = engine.submit_order(order)

    print(order.status)
    print(order.error_message)
    positions = engine.get_all_positions()

    for p in positions:
        print("\n[POSITION]")
        print("Symbol:", p.symbol)
        print("Side  :", p.side)
        print("Qty   :", p.quantity)
        print("Entry :", p.entry_price)
        print("SL    :", p.stop_loss)

if __name__ == "__main__":
    test_invalid_quantity()
    test_invalid_sl_buy()
    test_invalid_sl_sell()
    test_submit_order_flow()