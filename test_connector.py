from connectors.factory import ConnectorFactory

import connectors.mt5_connector
print(connectors.mt5_connector.__file__)
import MetaTrader5 as mt5
print(mt5.symbols_get())
config = {
    "login": 168516134,
    "password": "Anam.cool65",
    "server": "XMGlobal-MT5 2"
}

connector = ConnectorFactory.create("mt5", config)

connector.connect()
result = connector.place_market_order("BTCUSD", "buy", 0.01)
print(result)
print(connector.get_position("BTCUSD"))

import time
time.sleep(1)