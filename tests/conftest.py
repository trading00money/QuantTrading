import pytest
import os
os.environ["PYTHONUTF8"] = "1"

# @pytest.fixture(autouse=True)
# def auto_mock_risk_gateway(request, monkeypatch):

#     # 🔥 SKIP MOCK untuk test kritis
#     if "no_mock" in request.keywords:
#         return

#     from core.risk_gateway import RiskGateway

#     def mock_eval(self, **kwargs):
#         class Decision:
#             approved = True
#             position_size = 0.01
#             reason = "mock"
#             risk_level = "low"
#         return Decision()

#     monkeypatch.setattr(
#         RiskGateway,
#         "evaluate_trade",
#         mock_eval
#     )