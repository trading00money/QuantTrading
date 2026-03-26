import pandas as pd
from loguru import logger
from typing import Dict, Tuple, Optional

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    high_low = data['high'] - data['low']
    high_close = (data['high'] - data['close'].shift()).abs()
    low_close = (data['low'] - data['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

class RiskManager:
    """
    Manages risk parameters for trades, such as stop loss and take profit levels.
    """
    def __init__(self, risk_config: Dict, price_data: pd.DataFrame):
        """
        Initializes the RiskManager.

        Args:
            risk_config (Dict): The risk configuration dictionary.
            price_data (pd.DataFrame): The full history of price data, needed for ATR calculation.
        """
        self.config = risk_config
        self.price_data = price_data
        self._prepare_indicators()
        logger.info("RiskManager initialized.")

    def _prepare_indicators(self):
        """Pre-calculates any indicators needed for risk management, like ATR."""
        atr_period = self.config.get("atr_period", 14)
        self.price_data['atr'] = calculate_atr(self.price_data, period=atr_period)

    def get_exit_levels(
        self,
        entry_price: float,
        trade_side: str,
        timestamp: pd.Timestamp,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Optional[Tuple[float, float]]:

        # ✅ PRIORITY: pakai dari signal engine
        if stop_loss is not None and take_profit is not None:
            if stop_loss <= 0 or take_profit <= 0:
                return None
            return stop_loss, take_profit

        # ⚠️ FALLBACK: logic lama (sementara)
        logger.warning("Fallback ke legacy SL/TP calculation")

        sl_method = self.config.get("stop_loss_method", "percentage")
        tp_method = self.config.get("take_profit_method", "rr_ratio")
        rr_ratio = self.config.get("risk_reward_ratio", 2.0)

        stop_loss = 0.0

        if sl_method == "atr":
            atr_multiplier = self.config.get("atr_multiplier", 2.0)
            atr_value = self.price_data.at[timestamp, 'atr']

            if pd.isna(atr_value):
                sl_method = "percentage"
            else:
                if trade_side == 'long':
                    stop_loss = entry_price - (atr_value * atr_multiplier)
                else:
                    stop_loss = entry_price + (atr_value * atr_multiplier)

        if sl_method == "percentage":
            sl_pct = self.config.get("stop_loss_percentage", 2.0) / 100
            if trade_side == 'long':
                stop_loss = entry_price * (1 - sl_pct)
            else:
                stop_loss = entry_price * (1 + sl_pct)

        if stop_loss <= 0:
            return None

        risk_per_share = abs(entry_price - stop_loss)

        if trade_side == 'long':
            take_profit = entry_price + (risk_per_share * rr_ratio)
        else:
            take_profit = entry_price - (risk_per_share * rr_ratio)

        return stop_loss, take_profit

# Example Usage
if __name__ == "__main__":
    from core.data_feed import DataFeed
    mock_risk_config = {
        "stop_loss_method": "atr",
        "atr_period": 14,
        "atr_multiplier": 2.5,
        "take_profit_method": "rr_ratio",
        "risk_reward_ratio": 3.0
    }

    data_feed = DataFeed({})
    price_data = self.get_historical_data("BTC/USDT", "1d", "2022-01-01")

    if price_data is not None:
        risk_manager = RiskManager(mock_risk_config, price_data)

        # Simulate a long trade on the last day
        last_day = price_data.iloc[-1]
        entry_ts = last_day.name
        entry_p = last_day.close

        entry, sl, tp = signal_engine._calculate_levels(...)
        sl, tp = risk_manager.get_exit_levels(entry, side, ts, sl, tp)

        print("--- Risk Manager Test (Long Trade) ---")
        print(f"Trade Entry Date: {entry_ts.date()}")
        print(f"Entry Price: ${entry_p:,.2f}")
        print(f"ATR on Entry: ${risk_manager.price_data.at[entry_ts, 'atr']:,.2f}")
        print(f"Stop Loss: ${sl:,.2f}")
        print(f"Take Profit: ${tp:,.2f}")
        print("--------------------------------------")
