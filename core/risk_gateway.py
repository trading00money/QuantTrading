from core.risk_engine import RiskEngine, RiskConfig
from core.portfolio_manager import PortfolioManager
from dataclasses import dataclass
from typing import Dict, Optional, List
import threading
from loguru import logger
import pandas as pd


@dataclass
class RiskDecision:
    approved: bool
    position_size: float = 0.0
    reason: str = ''
    risk_level: str = 'low'


class RiskGateway:
    """SATU-SATUNYA pintu untuk semua keputusan risk."""

    def __init__(self, config: Dict):
        self.risk_engine = RiskEngine(
            RiskConfig(**config.get('risk_engine', {}))
        )
        self.portfolio_mgr = PortfolioManager(
            config.get('portfolio', {})
        )
        self._lock = threading.Lock()

    # ================================
    # MAIN ENTRY
    # ================================
    def evaluate_trade(
        self,
        symbol,
        side,
        entry_price,
        stop_loss,
        account_balance,
        open_positions=None,
        price_data: Optional[Dict[str, pd.Series]] = None  # 🔥 NEW
    ):
        with self._lock:

            # STEP 1: Kill switch
            if self.risk_engine.kill_switch_active:
                return RiskDecision(
                    approved=False,
                    reason='KILL SWITCH AKTIF'
                )

            # STEP 2: Risk check
            result = self.risk_engine.check_trade_risk(
                symbol=symbol,
                side=side,
                order_type='market',
                quantity=0,
                price=entry_price,
                stop_loss=stop_loss,
                account_balance=account_balance
            )

            if not result.passed:
                return RiskDecision(
                    approved=False,
                    reason='; '.join(result.messages)
                )

            # STEP 3: Position sizing
            size = self.portfolio_mgr.calculate_position_size(
                account_balance,
                entry_price,
                stop_loss
            )

            if size <= 0:
                return RiskDecision(
                    approved=False,
                    reason='Position size invalid'
                )

            # STEP 4: Correlation (REAL VERSION)
            if open_positions is None:
                open_positions = self.portfolio_mgr.get_open_positions()

            max_corr = self.risk_engine.config.max_correlated_positions or 3

            # 👉 fallback kalau tidak ada data harga
            if price_data is None:
                corr_count = self._count_correlated_simple(symbol, open_positions)
            else:
                corr_matrix = self._build_corr_matrix(price_data)
                corr_count = self._count_correlated_real(
                    symbol,
                    open_positions,
                    corr_matrix
                )

            # HARD LIMIT
            if corr_count + 1 >= max_corr:
                return RiskDecision(
                    approved=False,
                    reason=f"Max correlated positions ({corr_count + 1}) reached"
                )

            # SIZE REDUCTION
            if corr_count >= 2:
                reduction = min(0.5, 0.2 * corr_count)
                size *= (1 - reduction)

                logger.warning(
                    f"{symbol}: {corr_count} correlated → size reduced"
                )

            return RiskDecision(
                approved=True,
                position_size=size,
                risk_level=result.risk_level.value
            )

    # ================================
    # SIMPLE (FALLBACK)
    # ================================
    def _count_correlated_simple(self, symbol, positions):
        symbol = symbol.upper()
        base = symbol[:3]

        count = 0
        for p in positions:
            sym = p.symbol if hasattr(p, "symbol") else p.get("symbol", "")
            sym = sym.upper()

            if sym.startswith(base):
                count += 1

        return count

    # ================================
    # REAL CORRELATION
    # ================================
    def _build_corr_matrix(self, price_data: Dict[str, pd.Series]) -> pd.DataFrame:
        df = pd.DataFrame(price_data)

        # return-based correlation (WAJIB)
        returns = df.pct_change().dropna()

        return returns.corr()

    def _count_correlated_real(
        self,
        symbol,
        positions,
        corr_matrix,
        threshold: float = 0.7
    ):
        symbol = symbol.upper()

        if symbol not in corr_matrix:
            return 0

        count = 0

        for p in positions:
            sym = p.symbol if hasattr(p, "symbol") else p.get("symbol", "")
            sym = sym.upper()

            if sym == symbol:
                continue

            if sym not in corr_matrix:
                continue

            corr = corr_matrix.loc[symbol, sym]

            if corr >= threshold:
                count += 1

        return count