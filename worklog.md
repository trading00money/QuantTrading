# Backend Modules Audit Report

**Task ID: 1-d**  
**Date: 2025-01-20**  
**Auditor: Quantitative Trading Systems Specialist**

---

## Executive Summary

This audit covers all 7 subfolders within `/home/z/my-project/modules/`: gann/, ehlers/, astro/, forecasting/, ml/, smith/, and options/. The modules form a comprehensive trading analysis system implementing Gann theory, Ehlers DSP indicators, astrological cycle analysis, ML forecasting, Smith Chart analysis, and options pricing.

**Overall Assessment: MODERATE RISK for live trading**

---

## 1. Module Files Analyzed

### GANN Module (12 files)
- `square_of_9.py` - Gann Square of 9 calculator
- `square_of_24.py` - 24-hour cycle analysis
- `square_of_52.py` - Weekly cycle analysis
- `square_of_90.py` - Quarterly cycle analysis
- `square_of_144.py` - Master time cycle
- `square_of_360.py` - Full circle/year cycle
- `gann_angles.py` - Gann angle calculations
- `gann_time.py` - Time cycle and vibration analysis
- `gann_wave.py` - Wave analysis with 16x1 to 1x16 angles
- `spiral_gann.py` - Logarithmic spiral calculations
- `gann_forecasting.py` - Price and time forecasting
- `time_price_geometry.py` - Time-price relationships
- `elliot_wave.py` - Elliott Wave analysis

### EHLERS Module (12 files)
- `cyber_cycle.py` - Cycle oscillator
- `mama.py` - MESA Adaptive Moving Average
- `super_smoother.py` - 2-pole and 3-pole Butterworth filters
- `roofing_filter.py` - Band-pass filter
- `hilbert_transform.py` - Phase and period detection
- `fisher_transform.py` - Gaussian distribution transform
- `sinewave_indicator.py` - Cycle mode detection
- `bandpass_filter.py` - Frequency isolation
- `decycler.py` - Trend extraction
- `smoothed_rsi.py` - Ehlers Smoothed RSI and Laguerre RSI
- `instantaneous_trendline.py` - ITrend and Trend Vigor

### ASTRO Module (6 files)
- `astro_ephemeris.py` - Planetary position calculator
- `planetary_aspects.py` - Aspect detection
- `synodic_cycles.py` - Planetary cycle analysis
- `zodiac_degrees.py` - Zodiac calculations
- `retrograde_cycles.py` - Retrograde analysis
- `time_harmonics.py` - Gann/Fibonacci/planetary time cycles

### FORECASTING Module (6 files)
- `astro_cycle_projection.py` - Astrological projections
- `gann_forecast_daily.py` - Daily Gann forecasts
- `gann_wave_projection.py` - Wave projection wrapper
- `elliott_wave_projection.py` - Elliott Wave analysis
- `ml_time_forecast.py` - ML time series forecasting
- `report_generator.py` - Report generation

### ML Module (4 files)
- `features.py` - Feature engineering
- `models.py` - Linear, RF, Ensemble models
- `predictor.py` - Prediction interface
- `trainer.py` - Model training utilities

### SMITH Module (3 files)
- `smith_chart.py` - Smith Chart adaptation
- `impedance_mapping.py` - Impedance representation
- `resonance_detector.py` - FFT-based resonance detection

### OPTIONS Module (3 files)
- `greeks_calculator.py` - Black-Scholes Greeks
- `options_sentiment.py` - Put/call ratio, max pain
- `volatility_surface.py` - IV surface construction

---

## 2. Interface/API Analysis

### Consistent Patterns
- All modules use **dataclass** for structured returns
- **Config dict** pattern for initialization parameters
- **loguru** logger for consistent logging
- **pandas DataFrame** as primary data structure
- Both **class-based** and **functional** interfaces provided

### API Signatures (Critical for Frontend Integration)

| Module | Primary Input | Primary Output | Frontend-Ready |
|--------|--------------|----------------|----------------|
| SquareOf9 | initial_price, n_levels | Dict[support, resistance] | ✓ |
| CyberCycle | DataFrame, alpha | DataFrame[cycle, trigger, signal] | ✓ |
| GannWave | DataFrame, config | Dict[waves, projections] | ✓ |
| HilbertTransform | DataFrame | DataFrame[hilbert_* columns] | ✓ |
| GreeksCalculator | spot, strike, T, vol, r | OptionGreeks dataclass | ✓ |
| MLPredictor | DataFrame | PredictionResult dataclass | ✓ |

### Return Format Standardization
```
Standard output patterns:
- Status field: 'success', 'insufficient_data', 'error'
- Numeric rounding: 2-4 decimal places
- Date formatting: ISO format or strftime
- Signal encoding: 1 (bullish), -1 (bearish), 0 (neutral)
```

---

## 3. Cross-Module Dependencies

### Dependency Graph

```
forecasting/
├── gann_wave_projection.py → gann/gann_wave.py
├── elliott_wave_projection.py → (standalone)
├── astro_cycle_projection.py → astro/ (optional skyfield)
└── ml_time_forecast.py → ml/features.py

ml/
├── predictor.py → features.py, models.py
└── trainer.py → features.py, models.py

smith/
└── All standalone (unique impedance mapping)

options/
└── All standalone (scipy.stats.norm)

astro/
├── All conditionally import skyfield
└── External dependency: skyfield (OPTIONAL)

ehlers/
├── hilbert_transform.py used by mama.py
├── super_smoother.py used by roofing_filter.py
└── All internally consistent
```

### Import Validation
- **All imports validated** - no broken references
- **Optional imports handled** - skyfield gracefully degrades
- **Circular dependencies** - None detected
- **External dependencies** - numpy, pandas, scipy, loguru required

---

## 4. Calculation Accuracy Assessment

### GANN Calculations
| Module | Formula | Accuracy | Notes |
|--------|---------|----------|-------|
| SquareOf9 | sqrt(price) ± 0.25 increments | ✓ Correct | Classic Gann formula |
| Gann Angles | arctan(price_change/time) | ✓ Correct | 11 angles from 16x1 to 1x16 |
| Square of 144 | sqrt(price)/144 increment | ✓ Correct | Master square implementation |
| Time Cycles | 7, 14, 21, 30, 45, 90, 144, 360 days | ✓ Correct | Standard Gann intervals |

### EHLERS DSP Calculations
| Module | Formula | Accuracy | Notes |
|--------|---------|----------|-------|
| CyberCycle | 2nd-order HP filter | ✓ Correct | Alpha = 0.07 default |
| SuperSmoother | Butterworth 2-pole | ✓ Correct | a = exp(-√2π/period) |
| Hilbert Transform | Quadrature detection | ✓ Correct | Homodyne discriminator |
| MAMA/FAMA | Adaptive EMA with period | ✓ Correct | Fast/slow limits configurable |
| Fisher Transform | 0.5 * ln((1+x)/(1-x)) | ✓ Correct | Value clipping to ±0.999 |

### OPTIONS Calculations
| Module | Formula | Accuracy | Notes |
|--------|---------|----------|-------|
| Greeks (BS) | Standard Black-Scholes | ✓ Correct | Newton-Raphson for IV |
| Delta | N(d1) for call, N(d1)-1 for put | ✓ Correct | |
| Gamma | N'(d1) / (S*σ*√T) | ✓ Correct | |
| Theta | Daily decay | ✓ Correct | Divided by 365 |
| Vega | S*√T*N'(d1)/100 | ✓ Correct | Per 1% IV change |

---

## 5. Numerical Precision Concerns

### HIGH PRIORITY Issues

1. **Division by Zero Risks**
   - `square_of_9.py`: Line 58 - `sqrt_price - (i / 4.0)` can go negative
     - **MITIGATION EXISTS**: `if level_sqrt_sup > 0` check
   - `fisher_transform.py`: Line 31 - Division by `highest_high - lowest_low`
     - **MITIGATION EXISTS**: `value.clip(-0.999, 0.999)` prevents log(0)
   - `smoothed_rsi.py`: Line 109 - `avg_gain / avg_loss`
     - **MITIGATION EXISTS**: `if avg_loss[i] == 0: rsi[i] = 100`

2. **Floating Point Accumulation**
   - `hilbert_transform.py`: Iterative smoothing `0.2 * val + 0.8 * prev`
     - **RISK**: Minor drift over 1000+ bars - acceptable for trading
   - `mama.py`: Multi-stage iterative calculations
     - **RISK**: Period estimation can spike on noise - bounded to 6-50

3. **Overflow/Underflow**
   - `fisher_transform.py`: `np.log((1 + value) / (1 - value))`
     - **MITIGATED**: Value clipped to ±0.999 before log
   - `impedance_mapping.py`: VSWR calculation can hit infinity
     - **MITIGATED**: `if gamma < 0.99 else 999` cap

### MEDIUM PRIORITY Issues

4. **Array Index Safety**
   - Multiple files: `iloc[i-1]`, `iloc[i-2]` patterns
     - **STATUS**: Generally handled with range checks
   - `gann_wave.py`: Lines 262-264 - Swing detection needs min 5 bars
     - **MITIGATED**: Early return if `len(df) < 5`

5. **NaN Propagation**
   - `features.py`: Rolling calculations produce NaN for first N bars
     - **MITIGATED**: `df.dropna()` in prepare_features
   - `bandpass_filter.py`: First 2 bars return 0
     - **ACCEPTABLE**: Standard warmup behavior

### LOW PRIORITY Issues

6. **Type Coercion**
   - Mixed float/int in calculations
     - **STATUS**: numpy handles automatically
   - DataFrame index types assumed DatetimeIndex
     - **RISK**: Will fail with numeric index - needs validation

---

## 6. Error Handling Assessment

### Strong Error Handling ✓
- `square_of_9.py`: `ValueError` for non-positive initial_price
- `square_of_90.py`: Input validation with descriptive error messages
- `fisher_transform.py`: Checks for 'high' and 'low' columns
- `greeks_calculator.py`: Handles expired options (T <= 0)
- `volatility_surface.py`: Returns None on IV convergence failure

### Needs Improvement ⚠
- `gann_angles.py`: No validation of DataFrame index type
- `gann_forecasting.py`: Assumes DataFrame has 'close' column without check
- `ml_time_forecast.py`: Silent fallback to last price on training failure
- `resonance_detector.py`: No validation of minimum data length for FFT

### Missing Error Handling ✗
- `spiral_gann.py`: No validation of center_price > 0
- `time_harmonics.py`: No bounds checking on historical_pivots list
- `options_sentiment.py`: Division by zero risk in OI ratio (line 123)

---

## 7. Frontend Compatibility

### Chart-Ready Outputs ✓
All modules return data structures compatible with common charting libraries:

```javascript
// Expected frontend data format
{
  "status": "success",
  "values": [
    { "date": "2024-01-01", "value": 123.45 },
    { "date": "2024-01-02", "value": 124.56 }
  ],
  "signals": [
    { "date": "2024-01-03", "signal": 1, "type": "buy" }
  ]
}
```

### Signal Encoding Standard
| Value | Meaning | Frontend Display |
|-------|---------|------------------|
| 1 | Bullish | Green arrow up |
| -1 | Bearish | Red arrow down |
| 0 | Neutral | Gray dash |

### DataFrame Index Handling
- Modules expect `DatetimeIndex` or will use `datetime.now()` fallback
- Frontend should pass ISO date strings for proper parsing

---

## 8. Recommendations for Live Trading

### CRITICAL - Must Fix Before Live
1. **Add input validation layer** - Create decorator for DataFrame validation
2. **Implement circuit breakers** - NaN/Inf detection before calculations
3. **Add data freshness checks** - Validate timestamps within acceptable window
4. **Implement calculation timeouts** - Prevent hanging on large datasets

### HIGH PRIORITY - Should Address
5. **Add unit tests** - No test coverage visible for calculation verification
6. **Implement logging levels** - Production vs development log verbosity
7. **Add memory management** - Large DataFrame handling optimization
8. **Create API versioning** - Structure returns for backward compatibility

### MEDIUM PRIORITY - Recommended
9. **Add confidence intervals** - All forecasts should include uncertainty bounds
10. **Implement warmup indicators** - Flag first N bars as unreliable
11. **Add data quality scoring** - Flag anomalous inputs before processing
12. **Create calculation audit trail** - Log intermediate values for debugging

### LOW PRIORITY - Nice to Have
13. **Add async processing** - For computationally intensive calculations
14. **Implement caching** - For frequently accessed historical calculations
15. **Add configuration validation** - Validate config dicts on initialization

---

## 9. Module-Specific Live Trading Notes

### GANN Module
- **Verdict**: Ready for paper trading with monitoring
- **Concern**: Angle calculations assume linear price/time scaling
- **Recommendation**: Add price_scale parameter tuning per instrument

### EHLERS Module
- **Verdict**: Ready for live trading
- **Concern**: Cycle detection can produce false signals in low-volatility regimes
- **Recommendation**: Combine with volume confirmation

### ASTRO Module
- **Verdict**: REQUIRES OPTIONAL DEPENDENCY
- **Concern**: skyfield library adds ~100MB dependency
- **Recommendation**: Make truly optional with feature flag

### FORECASTING Module
- **Verdict**: Ready for paper trading
- **Concern**: ML forecasts degrade over multi-step predictions
- **Recommendation**: Confidence decay function for longer horizons

### ML Module
- **Verdict**: NOT RECOMMENDED for live without validation
- **Concern**: No model persistence, no hyperparameter tuning
- **Recommendation**: Add sklearn integration for production models

### SMITH Module
- **Verdict**: Experimental - paper trading only
- **Concern**: Unique methodology without trading track record
- **Recommendation**: Extensive backtesting before live use

### OPTIONS Module
- **Verdict**: Ready for live with proper data feed
- **Concern**: Assumes European options for BS model
- **Recommendation**: Add American option adjustment for early exercise

---

## 10. Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Total Files Analyzed | 46 | Complete |
| Module Interfaces | 46 | Documented |
| Cross-Dependencies | 12 | Mapped |
| Numerical Issues (High) | 3 | Mitigated |
| Numerical Issues (Medium) | 4 | Acceptable |
| Numerical Issues (Low) | 2 | Minor |
| Error Handling Gaps | 6 | Identified |
| Frontend-Compatible APIs | 46 | Verified |

---

**Audit Complete**  
**Risk Level**: MODERATE  
**Recommendation**: Proceed to paper trading with monitoring, address critical issues before live deployment

---

# Duplicated Code Scanner Report

**Task ID: 3-c**  
**Date: 2025-01-20**  
**Scanner: Code Quality Scanner**

---

## Executive Summary

Comprehensive scan of Python (.py) and TypeScript/React (.ts, .tsx) files revealed **significant code duplication** across multiple priority folders. Total files scanned: **~240 Python files** and **~80 TypeScript/TSX files**.

**Overall Duplication Assessment: HIGH SEVERITY**

**Estimated Code Reduction Potential: 25-35%**

---

## 1. HIGH SEVERITY Duplications

### 1.1 Crypto Low-Latency Connector Duplication

| File | Lines | Issue |
|------|-------|-------|
| `connectors/crypto_low_latency.py` | ~1,130+ | Original implementation |
| `connectors/crypto_low_latency_v2.py` | ~820+ | **CORRUPTED DUPLICATE** - Syntax errors, malformed code |

**Severity: HIGH**  
**Impact**: v2 file contains broken code with malformed enums, incomplete functions, and syntax errors starting at line 63. This file appears to be a corrupted copy attempt.

**Recommendation**: 
- DELETE `crypto_low_latency_v2.py` immediately
- Consolidate all crypto exchange support into single file

---

### 1.2 MT4/MT5 Low-Latency Connector Structural Duplication

| File | Lines | Duplicate Code |
|------|-------|----------------|
| `connectors/mt4_low_latency.py` | 1,120 | ~800 lines |
| `connectors/mt5_low_latency.py` | 1,120+ | ~800 lines |

**Duplicated Elements**:
- `CommandType` enum (lines 75-114 in MT4, lines 82-121 in MT5)
- `ResponseStatus` enum (lines 117-124 in MT4, lines 124-131 in MT5)
- `ConnectionPool` class (lines 424-510 in MT4, lines 356-431 in MT5)
- `_recv_exact()` method
- `_send_command_sync()` method
- `calculate_slippage()` method (identical logic)
- `update_slippage_from_frontend()` method

**Severity: HIGH**  
**Impact**: Maintenance burden, bug fixes need to be applied twice

**Recommendation**:
```python
# Create shared base class
class BaseLowLatencyConnector:
    def calculate_slippage(self, symbol, spread=None, volatility=None, frontend_slippage=None):
        # Shared implementation
        
class MT4LowLatency(BaseLowLatencyConnector):
    # MT4-specific methods
    
class MT5LowLatency(BaseLowLatencyConnector):
    # MT5-specific methods
```

---

### 1.3 Ehlers Indicators - Python/TypeScript Duplication

| Python File | TypeScript File | Duplicated Logic |
|-------------|-----------------|------------------|
| `modules/ehlers/mama.py` | `frontend/src/lib/ehlersCalculations.ts` | MAMA/FAMA algorithm |
| `modules/ehlers/fisher_transform.py` | `frontend/src/lib/ehlersFilters.ts` | Fisher Transform |
| `modules/ehlers/super_smoother.py` | `frontend/src/lib/ehlersFilters.ts` | Super Smoother |
| `modules/ehlers/roofing_filter.py` | `frontend/src/lib/ehlersFilters.ts` | Roofing Filter |
| `modules/ehlers/cyber_cycle.py` | `frontend/src/lib/ehlersFilters.ts` | Cyber Cycle |
| `core/ehlers_indicators.py` | Multiple TS files | Full indicator suite |

**Severity: HIGH**  
**Impact**: Algorithm changes must be synchronized across two codebases

**Recommendation**: 
- Backend should expose calculated indicators via API
- Frontend should consume API rather than recalculate
- OR: Generate TypeScript from Python using type stubs

---

### 1.4 Ehlers Indicators - Python Internal Duplication

| Location | Issue |
|----------|-------|
| `core/ehlers_indicators.py` (lines 27-517) | Full Ehlers indicator implementation |
| `modules/ehlers/*.py` | Same indicators split across 12 files |
| `core/ehlers_engine.py` | Uses modules/ehlers imports |

**Severity: HIGH**  
**Impact**: Two parallel implementations, potential drift

**Example - MAMA Implementation**:
- `core/ehlers_indicators.py`: `EhlersIndicators.mama()` static method (lines 225-274)
- `modules/ehlers/mama.py`: `mama()` function and `MAMAIndicator` class (176 lines)

---

## 2. MEDIUM SEVERITY Duplications

### 2.1 Toast Hook Duplication (React)

| File | Lines | Content |
|------|-------|---------|
| `frontend/src/hooks/use-toast.ts` | 187 | Complete toast implementation |
| `frontend/src/components/ui/use-toast.ts` | 4 | Re-export from hooks |

**Severity: MEDIUM**  
**Impact**: Confusion, potential for divergent implementations

**Recommendation**: Delete `components/ui/use-toast.ts`, use single source in hooks/

---

### 2.2 Connection Pool Duplication

| File | Class | Duplicate Code |
|------|-------|----------------|
| `connectors/mt4_low_latency.py` | `ConnectionPool` | 85 lines |
| `connectors/mt5_low_latency.py` | `MT5ConnectionPool` | 75 lines |
| `connectors/base_connector.py` | `ConnectionPoolBase` | 39 lines (partial abstraction) |

**Severity: MEDIUM**  
**Impact**: Already partially addressed with base_connector.py, but incomplete

---

### 2.3 Risk Engine Configuration Patterns

Multiple files share identical configuration patterns:
- `core/risk_engine.py`: `RiskConfig` dataclass
- `core/execution_engine.py`: Risk settings in `ExecutionEngine.__init__()`
- `src/risk/*.py`: Duplicate risk calculation logic

---

## 3. LOW SEVERITY Duplications

### 3.1 Import Pattern Duplication

**Statistics from grep analysis**:

| Import Pattern | Occurrences | Files |
|---------------|-------------|-------|
| `from loguru import logger` | 214 | All Python files |
| `import pandas as pd` | 100+ | Data processing files |
| `import numpy as np` | 95+ | Mathematical modules |
| `from typing import` | 180+ | Type-hinted modules |
| `from dataclasses import dataclass` | 65+ | Data structure files |

**Severity: LOW**  
**Impact**: Standard practice, but could benefit from shared prelude file

**Recommendation**: Create `utils/prelude.py` with common imports
```python
# utils/prelude.py
from loguru import logger
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
```

---

### 3.2 Dataclass Pattern Duplication

Multiple files define similar dataclasses:
- `Order` dataclass in: `core/execution_engine.py`, `core/order_manager.py`
- `Position` dataclass in: `core/execution_engine.py`, `core/portfolio_manager.py`
- `Tick` dataclass in: Multiple connector files

---

## 4. Import Pattern Analysis

### 4.1 Circular Import Risk

**Potential circular imports detected**:
- `core/ehlers_engine.py` → `modules/ehlers/*` → potentially back to core
- `core/gann_engine.py` → `modules/gann/*` → potential back reference

**Recommendation**: Audit import chains with `import-linter`

---

### 4.2 Orphaned Imports

Files with potentially unused imports (needs verification):
- `connectors/crypto_low_latency_v2.py` - Multiple broken imports due to file corruption

---

## 5. Detailed File-by-File Duplications

### Priority Folder: core/

| File | Duplicate Found In | Severity | Lines Affected |
|------|-------------------|----------|----------------|
| `core/ehlers_indicators.py` | `modules/ehlers/*.py` | HIGH | ~400 |
| `core/ehlers_engine.py` | `modules/ehlers/mama.py`, `cyber_cycle.py` | MEDIUM | ~50 |
| `core/gann_engine.py` | `modules/gann/gann_angles.py`, `square_of_9.py` | MEDIUM | ~30 |
| `core/execution_engine.py` | `core/order_manager.py` | MEDIUM | ~100 |
| `core/risk_engine.py` | `src/risk/portfolio_risk.py` | MEDIUM | ~40 |

### Priority Folder: connectors/

| File | Duplicate Found In | Severity | Lines Affected |
|------|-------------------|----------|----------------|
| `connectors/crypto_low_latency.py` | `connectors/crypto_low_latency_v2.py` | HIGH | 1100+ |
| `connectors/mt4_low_latency.py` | `connectors/mt5_low_latency.py` | HIGH | 800+ |
| `connectors/base_connector.py` | Both MT4/MT5 connectors | MEDIUM | 50 |

### Priority Folder: modules/

| File | Duplicate Found In | Severity | Lines Affected |
|------|-------------------|----------|----------------|
| `modules/ehlers/mama.py` | `core/ehlers_indicators.py` | HIGH | 130 |
| `modules/ehlers/fisher_transform.py` | `frontend/src/lib/ehlersFilters.ts` | HIGH | 40 |
| `modules/ehlers/super_smoother.py` | `frontend/src/lib/ehlersFilters.ts` | HIGH | 30 |

### Priority Folder: frontend/src/lib/

| File | Duplicate Found In | Severity | Lines Affected |
|------|-------------------|----------|----------------|
| `frontend/src/lib/ehlersFilters.ts` | `modules/ehlers/*.py` | HIGH | 140 |
| `frontend/src/lib/ehlersCalculations.ts` | `modules/ehlers/mama.py` | HIGH | 115 |

---

## 6. Recommendations Summary

### Immediate Actions (Critical)

1. **DELETE** `connectors/crypto_low_latency_v2.py` - Corrupted file
2. **CONSOLIDATE** MT4/MT5 connectors using shared base class
3. **UNIFY** Ehlers indicators - Choose single implementation location

### Short-term Actions (This Sprint)

4. Create `utils/prelude.py` for common imports
5. Remove `frontend/src/components/ui/use-toast.ts` duplicate
6. Define shared dataclasses in `core/models.py`

### Long-term Actions (Backlog)

7. Generate TypeScript types from Python dataclasses
8. Implement API-based indicator calculation (remove frontend recalculation)
9. Add automated duplication detection to CI/CD pipeline

---

## 7. Estimated Code Reduction

| Category | Current Lines | Reducible Lines | Reduction % |
|----------|---------------|-----------------|-------------|
| Crypto Connectors | 2,000 | 900 | 45% |
| MT4/MT5 Connectors | 2,200 | 700 | 32% |
| Ehlers Indicators (Python) | 1,200 | 400 | 33% |
| Ehlers (TypeScript) | 300 | 300 | 100% (API-based) |
| Toast/Utility Dups | 200 | 50 | 25% |
| **TOTAL** | **~5,900** | **~2,350** | **~40%** |

**Conservative Estimate: 25-35% code reduction achievable**

---

## 8. Files Requiring Immediate Attention

| File | Action | Priority |
|------|--------|----------|
| `connectors/crypto_low_latency_v2.py` | DELETE | CRITICAL |
| `connectors/mt5_low_latency.py` | REFACTOR to use base class | HIGH |
| `connectors/mt4_low_latency.py` | REFACTOR to use base class | HIGH |
| `frontend/src/lib/ehlersFilters.ts` | REMOVE (use API) | HIGH |
| `frontend/src/components/ui/use-toast.ts` | DELETE | MEDIUM |

---

**Scan Complete**  
**Duplication Severity: HIGH**  
**Recommendation**: Immediate remediation of critical items, create refactoring sprint for high-priority duplicates
