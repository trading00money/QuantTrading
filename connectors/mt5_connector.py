import MetaTrader5 as mt5
import pandas as pd
from loguru import logger


class MT5Connector:
    def __init__(self, config):
        self.login = config["login"]
        self.password = config["password"]
        self.server = config["server"]
        self.connected = False
        self.config = config

    # def connect(self):
    #     if not mt5.initialize(
    #         login=self.login,
    #         password=self.password,
    #         server=self.server
    #     ):
    #         logger.error(f"MT5 init failed: {mt5.last_error()}")
    #         return False

    #     self.connected = True
    #     logger.success("MT5 connected")
    #     return True
    def connect(self):
        import MetaTrader5 as mt5

        if not mt5.initialize(
            path=self.config.get("path"),
            login=self.config.get("login"),
            password=self.config.get("password"),
            server=self.config.get("server")
        ):
            raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

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

    def get_price(self, symbol: str):
        import MetaTrader5 as mt5

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise RuntimeError(f"Tidak bisa ambil harga untuk {symbol}")

        return {
            "bid": tick.bid,
            "ask": tick.ask
        }

    # def place_order(self, symbol, volume, order_type):
    #     price = mt5.symbol_info_tick(symbol).ask

    #     request = {
    #         "action": mt5.TRADE_ACTION_DEAL,
    #         "symbol": symbol,
    #         "volume": qty,
    #         "type": mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL,
    #         "price": price,
    #         "sl": stop_loss,
    #         "tp": take_profit,
    #         "deviation": 20,
    #         "magic": 123456,
    #         "comment": "auto trade",
    #         "type_time": mt5.ORDER_TIME_GTC,
    #         "type_filling": mt5.ORDER_FILLING_IOC,
    #     }

    #     result = mt5.order_send(request)
    #     return result
    
    def place_market_order(
        self,
        symbol,
        side,
        qty,
        stop_loss=None,
        take_profit=None
    ):
        import MetaTrader5 as mt5

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Tidak bisa ambil tick {symbol}")

        price = tick.ask if side == "BUY" else tick.bid

        # ========================
        # VALIDASI STOP LEVEL
        # ========================
        info = mt5.symbol_info(symbol)
        point = info.point
        min_distance = info.trade_stops_level * point

        if stop_loss:
            if abs(price - stop_loss) < min_distance:
                raise ValueError(f"SL terlalu dekat (min: {min_distance})")

        if take_profit:
            if abs(price - take_profit) < min_distance:
                raise ValueError(f"TP terlalu dekat (min: {min_distance})")

        # ========================
        # REQUEST
        # ========================
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": qty,
            "type": mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": 20,
            "magic": 123456,
            "comment": "auto trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            raise RuntimeError(f"order_send gagal: {mt5.last_error()}")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Order gagal: {result.retcode} | {result.comment}")

        return {
            "order_id": result.order,
            "price": result.price,
            "filled_qty": qty
        }

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