import pytest
import pandas as pd
import numpy as np
import numpy as np
from core.risk_gateway import RiskGateway

def generate_correlated_series(base, noise=0.01):
    return base + np.random.normal(0, noise, len(base))

@pytest.fixture
def base_config():
    return {
        "risk_engine": {
            "max_correlated_positions": 3
        },
        "portfolio": {}
    }


def test_real_correlation_size_reduction(base_config):
    base_config["risk_engine"]["max_correlated_positions"] = 5

    rg = RiskGateway(base_config)

    # 🔥 buat data harga
    base = np.cumsum(np.random.randn(100))

    btc = pd.Series(base)
    eth = pd.Series(generate_correlated_series(base))
    sol = pd.Series(generate_correlated_series(base))

    price_data = {
        "BTCUSDT": btc,
        "ETHUSDT": eth,
        "SOLUSDT": sol
    }

    open_positions = [
        {"symbol": "ETHUSDT"},
        {"symbol": "SOLUSDT"},
    ]

    decision = rg.evaluate_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        stop_loss=90,
        account_balance=10000,
        open_positions=open_positions,
        price_data=price_data
    )

    normal_size = rg.portfolio_mgr.calculate_position_size(10000, 100, 90)

    assert decision.approved is True
    assert decision.position_size < normal_size


def test_real_correlation_rejection(base_config):
    rg = RiskGateway(base_config)

    base = np.cumsum(np.random.randn(100))

    btc = pd.Series(base)
    eth = pd.Series(generate_correlated_series(base))
    sol = pd.Series(generate_correlated_series(base))

    price_data = {
        "BTCUSDT": btc,
        "ETHUSDT": eth,
        "SOLUSDT": sol
    }

    open_positions = [
        {"symbol": "ETHUSDT"},
        {"symbol": "SOLUSDT"},
        {"symbol": "BTCUSDT"},
    ]

    decision = rg.evaluate_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        stop_loss=90,
        account_balance=10000,
        open_positions=open_positions,
        price_data=price_data
    )

    assert decision.approved is False


def test_real_correlation_low_corr_no_reduction(base_config):
    rg = RiskGateway(base_config)

    # 🔥 data tidak correlated
    btc = pd.Series(np.cumsum(np.random.randn(100)))
    eur = pd.Series(np.cumsum(np.random.randn(100)))  # random beda

    price_data = {
        "BTCUSDT": btc,
        "EURUSD": eur
    }

    open_positions = [
        {"symbol": "EURUSD"},
    ]

    decision = rg.evaluate_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        stop_loss=90,
        account_balance=10000,
        open_positions=open_positions,
        price_data=price_data
    )

    normal_size = rg.portfolio_mgr.calculate_position_size(10000, 100, 90)

    assert decision.approved is True
    assert decision.position_size == normal_size