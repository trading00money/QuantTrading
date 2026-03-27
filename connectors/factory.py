from connectors.binance_connector import BinanceConnector
from connectors.mt5_connector import MT5Connector

class ConnectorFactory:

    @staticmethod
    def create(connector_type, config):
        if connector_type == "binance":
            return BinanceConnector(config)
        elif connector_type == "mt5":
            return MT5Connector(config)
        else:
            raise ValueError("Unknown connector")