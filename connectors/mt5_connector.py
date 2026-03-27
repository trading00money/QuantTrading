import MetaTrader5 as mt5
import pandas as pd
from loguru import logger


class MT5Connector:
    def __init__(self, config):
        self.login = config["login"]
        self.password = config["password"]
        self.server = config["server"]
        self.connected = False

    def connect(self):
        if not mt5.initialize(
            login=self.login,
            password=self.password,
            server=self.server
        ):
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False

        self.connected = True
        logger.success("MT5 connected")
        return True

    def get_historical_data(self, symbol, timeframe, bars=500):
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }

        rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, bars)

        if rates is None:
            logger.error("Failed to get rates")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        return df

    def place_order(self, symbol, volume, order_type):
        price = mt5.symbol_info_tick(symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "AI Trade",
            "type_filling": mt5.ORDER_FILLING_IOC,  # ← INI YANG KURANG
        }

        result = mt5.order_send(request)
        return result
    
    def place_market_order(self, symbol, side, qty):
        return self.place_order(symbol, qty, side.upper())

    def get_position(self, symbol):
        positions = mt5.positions_get(symbol=symbol)

        if not positions:
            return None

        results = []
        for p in positions:
            results.append({
                "symbol": p.symbol,
                "volume": p.volume,
                "type": p.type,
                "price_open": p.price_open,
                "profit": p.profit,
                "ticket": p.ticket
            })

        return results