import MetaTrader5 as mt5
from core.execution_engine import ExecutionEngine
from core.enums import BrokerType
# INIT MT5
mt5.initialize()

symbol = "BTCUSD"
mt5.symbol_select(symbol, True)

tick = mt5.symbol_info_tick(symbol)
price = tick.ask

sl = price - 500
tp = price + 500

# INIT ENGINE
config = {
    "broker_config": {
        "metatrader5": {
            "enabled": True,
            "login": 168516134,           # ⚠️ akun MT5 kamu
            "password": "Anam.cool65",
            "server": "XMGlobal-MT5 2",   # contoh: "ICMarketsSC-Demo"
            "path": r"C:\Program Files\MetaTrader 5\terminal64.exe"
        }
    }
}

engine = ExecutionEngine(config=config)

# TEST ORDER
order = engine.buy_market(
    symbol=symbol,
    quantity=0.01,
    stop_loss=sl,
    take_profit=tp,
    broker=BrokerType.MT5
)

print(order)