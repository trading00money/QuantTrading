"""
AI Signal Engine (Async)
Comprehensive signal generation combining Gann, Astrology, Ehlers DSP, and ML models.
Fully async implementation with parallel execution and thread-safe operations.
"""
import asyncio
import numpy as np
import pandas as pd
from loguru import logger
from modules.gann.square_of_9 import SquareOf9
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor
import functools


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class AnalysisError(Exception):
    """Base exception for analysis errors."""
    def __init__(self, source: str, message: str, original_error: Optional[Exception] = None):
        self.source = source
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{source}] {message}")


@dataclass
class SignalComponent:
    """Individual signal component from a specific engine."""
    source: str  # 'gann', 'astro', 'ehlers', 'ml', 'pattern'
    signal: SignalType
    confidence: float  # 0-100
    weight: float  # Contribution weight
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class AISignal:
    """Complete AI trading signal."""
    symbol: str
    timeframe: str
    signal: SignalType
    confidence: float  # 0-100
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    components: List[SignalComponent] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    model_attribution: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    valid_until: datetime = None
    metadata: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'signal': self.signal.value,
            'confidence': round(self.confidence, 2),
            'strength': self.strength.name,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward': round(self.risk_reward, 2),
            'reasons': self.reasons,
            'model_attribution': self.model_attribution,
            'timestamp': self.timestamp.isoformat(),
            'errors': self.errors,
            'components': [
                {
                    'source': c.source,
                    'signal': c.signal.value,
                    'confidence': c.confidence,
                    'weight': c.weight,
                    'error': c.error
                } for c in self.components
            ]
        }


class AISignalEngine:
    """
    Main AI Signal Engine that combines multiple analysis methods.
    
    Async implementation with:
    - Parallel execution of all analysis modules
    - Thread-safe operations with async locks
    - Comprehensive error handling
    - Timeout support for each analysis module
    
    Integrates:
    - WD Gann modules (Square of 9, 24, 52, 90, 144, 360)
    - Gann Time-Price Geometry
    - Astrology & market cycles
    - John Ehlers DSP indicators
    - Machine Learning models
    - Pattern Recognition
    """
    
    # Default weights for each component
    DEFAULT_WEIGHTS = {
        'gann': 0.30,       # ← naik 5%
        'astro': 0.10,      # ← turun 5% (belum tervalidasi)
        'ehlers': 0.30,     # ← naik 10% (setelah fix QW1)
        'ml': 0.00,         # ← DISABLED sampai model sungguhan siap
        'pattern': 0.15,    # ← naik 5% (setelah fix QW3)
        'options_flow': 0.05
    }
    
    # Default timeouts for each analysis module (in seconds)
    DEFAULT_TIMEOUTS = {
        'gann': 5.0,
        'astro': 3.0,
        'ehlers': 4.0,
        'ml': 10.0,
        'pattern': 3.0
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weights = self.config.get('weights', self.DEFAULT_WEIGHTS.copy())
        self.timeouts = self.config.get('timeouts', self.DEFAULT_TIMEOUTS.copy())
        
        # Initialize engines (lazy loading)
        self._gann_engine = None
        self._astro_engine = None
        self._ehlers_engine = None
        self._ml_engine = None
        self._pattern_engine = None
        
        # Signal history with thread-safe access
        self.signal_history: List[AISignal] = []
        self._history_lock = asyncio.Lock()
        
        # Thread pool for CPU-bound operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache for frequently accessed data
        self._cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
        
        logger.info("AISignalEngine (Async) initialized")
    
    async def _run_in_executor(self, func: callable, *args, **kwargs) -> Any:
        """Run a synchronous function in the thread pool executor."""
        loop = asyncio.get_event_loop()
        partial_func = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(self._executor, partial_func)
    
    async def _safe_analyze(
        self,
        analyze_func: callable,
        source: str,
        *args,
        **kwargs
    ) -> Optional[SignalComponent]:
        """
        Safely execute an analysis function with timeout and error handling.
        
        Args:
            analyze_func: The async analysis function to execute
            source: Name of the analysis source (for error reporting)
            *args, **kwargs: Arguments to pass to the analysis function
            
        Returns:
            SignalComponent or None if analysis failed
        """
        timeout = self.timeouts.get(source, 5.0)
        
        try:
            result = await asyncio.wait_for(
                analyze_func(*args, **kwargs),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Analysis timed out after {timeout}s"
            logger.warning(f"[{source}] {error_msg}")
            return SignalComponent(
                source=source,
                signal=SignalType.HOLD,
                confidence=0.0,
                weight=0.0,
                error=error_msg
            )
            
        except AnalysisError as e:
            logger.warning(f"[{source}] Analysis error: {e.message}")
            return SignalComponent(
                source=source,
                signal=SignalType.HOLD,
                confidence=0.0,
                weight=0.0,
                error=str(e)
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[{source}] {error_msg}", exc_info=True)
            return SignalComponent(
                source=source,
                signal=SignalType.HOLD,
                confidence=0.0,
                weight=0.0,
                error=error_msg
            )
    
    async def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        timeframe: str = "H1",
        current_price: float = None
    ) -> AISignal:
        """
        Generate comprehensive AI trading signal with parallel analysis.
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            timeframe: Timeframe of the data
            current_price: Current market price
            
        Returns:
            AISignal with complete analysis
        """
        start_time = datetime.now()
        
        if current_price is None and len(data) > 0:
            current_price = data['close'].iloc[-1]
        
        # Run all analyses in parallel using asyncio.gather
        components, errors = await self._run_parallel_analyses(
            data=data,
            symbol=symbol,
            current_price=current_price
        )
        
        # Extract reasons from high-confidence components
        reasons = self._extract_reasons(components)
        
        # Combine signals
        final_signal, confidence, strength = self._combine_signals(components)
        
        # Calculate entry, SL, TP
        entry, sl, tp = self._calculate_levels(data, final_signal, current_price)
        
        # Calculate risk-reward
        risk_reward = self._calculate_risk_reward(entry, sl, tp, final_signal)
        
        # Build model attribution
        attribution = self._build_attribution(components)
        
        # Create final signal
        signal = AISignal(
            symbol=symbol,
            timeframe=timeframe,
            signal=final_signal,
            confidence=confidence,
            strength=strength,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=risk_reward,
            components=components,
            reasons=reasons,
            model_attribution=attribution,
            errors=errors,
            metadata={
                'data_points': len(data),
                'components_used': len([c for c in components if c.error is None]),
                'analysis_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        )
        
        # Store in history (thread-safe)
        async with self._history_lock:
            self.signal_history.append(signal)
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-500:]
        
        logger.info(f"Generated signal for {symbol}: {final_signal.value} ({confidence:.1f}%)")
        
        return signal
    
    async def _run_parallel_analyses(
        self,
        data: pd.DataFrame,
        symbol: str,
        current_price: float
    ) -> Tuple[List[SignalComponent], List[str]]:
        """
        Run all analysis modules in parallel using asyncio.gather.
        
        Returns:
            Tuple of (components list, errors list)
        """
        # Create analysis tasks
        tasks = [
            self._safe_analyze(self._analyze_gann, 'gann', data, current_price),
            self._safe_analyze(self._analyze_astro, 'astro', data, symbol),
            self._safe_analyze(self._analyze_ehlers, 'ehlers', data),
            self._safe_analyze(self._analyze_ml, 'ml', data),
            self._safe_analyze(self._analyze_patterns, 'pattern', data),
        ]
        
        # Run all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        components = []
        errors = []
        
        for i, result in enumerate(results):
            source = ['gann', 'astro', 'ehlers', 'ml', 'pattern'][i]
            
            if isinstance(result, Exception):
                error_msg = f"{source}: {str(result)}"
                errors.append(error_msg)
                logger.error(f"Analysis task failed: {error_msg}")
                components.append(SignalComponent(
                    source=source,
                    signal=SignalType.HOLD,
                    confidence=0.0,
                    weight=0.0,
                    error=str(result)
                ))
            elif result is not None:
                components.append(result)
                if result.error:
                    errors.append(f"{source}: {result.error}")
        
        return components, errors
    
    async def _analyze_gann(
        self,
        data: pd.DataFrame,
        current_price: float
    ) -> Optional[SignalComponent]:
        """Analyze using Gann methods (async)."""
        def _sync_analyze():
            if len(data) < 20:
                return None
            
            high = data['high'].max()
            low = data['low'].min()
            close = data['close'].iloc[-1]
            
            # Square of 9 analysis
            sq9 = SquareOf9(low)
            levels = sq9.get_levels(5)
            
            # Find nearest support/resistance
            supports = [l for l in levels.get('support', []) if l < current_price]
            resistances = [l for l in levels.get('resistance', []) if l > current_price]
            
            nearest_support = max(supports) if supports else low
            nearest_resistance = min(resistances) if resistances else high
            
            # Determine signal based on price position
            range_size = nearest_resistance - nearest_support
            price_position = (current_price - nearest_support) / range_size if range_size > 0 else 0.5
            
            if price_position < 0.3:
                signal = SignalType.BUY
                confidence = (0.3 - price_position) * 200 + 50
                reason = f"Price near Sq9 support ${nearest_support:.2f}"
            elif price_position > 0.7:
                signal = SignalType.SELL
                confidence = (price_position - 0.7) * 200 + 50
                reason = f"Price near Sq9 resistance ${nearest_resistance:.2f}"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Price in neutral zone"
            
            return SignalComponent(
                source='gann',
                signal=signal,
                confidence=min(95, confidence),
                weight=self.weights.get('gann', 0.25),
                details={
                    'reason': reason,
                    'nearest_support': nearest_support,
                    'nearest_resistance': nearest_resistance
                }
            )
        
        try:
            return await self._run_in_executor(_sync_analyze)
        except Exception as e:
            raise AnalysisError('gann', str(e), e)
    
    async def _analyze_astro(
        self,
        data: pd.DataFrame,
        symbol: str
    ) -> Optional[SignalComponent]:
        """Analyze using astrological cycles (async)."""
        def _sync_analyze():
            from modules.astro.synodic_cycles import SynodicCycleCalculator
            
            synodic = SynodicCycleCalculator()
            phases = synodic.get_current_cycle_phases()
            
            bullish_score = 0
            bearish_score = 0
            
            for phase in phases:
                if phase.get('phase_name') in ['new', 'first_quarter']:
                    bullish_score += 1
                elif phase.get('phase_name') in ['full', 'last_quarter']:
                    bearish_score += 1
            
            if bullish_score > bearish_score:
                signal = SignalType.BUY
                confidence = 50 + (bullish_score * 10)
                reason = f"Bullish astro cycles ({bullish_score} signals)"
            elif bearish_score > bullish_score:
                signal = SignalType.SELL
                confidence = 50 + (bearish_score * 10)
                reason = f"Bearish astro cycles ({bearish_score} signals)"
            else:
                signal = SignalType.HOLD
                confidence = 50
                reason = "Neutral astro cycles"
            
            return SignalComponent(
                source='astro',
                signal=signal,
                confidence=confidence,
                weight=self.weights.get('astro', 0.15),
                details={'reason': reason}
            )
        
        try:
            return await self._run_in_executor(_sync_analyze)
        except Exception as e:
            raise AnalysisError('astro', str(e), e)
    
    async def _analyze_ehlers(self, data: pd.DataFrame):
       def _sync_analyze():
           if len(data) < 50: return None
     
           from modules.ehlers.fisher_transform import fisher_transform
           from modules.ehlers.super_smoother import super_smoother
           from modules.ehlers.mama import mama
     
           signals = {'buy': 0, 'sell': 0, 'total': 0}
     
           # 1. Fisher Transform crossover (mean-reversion)
           fisher_df = fisher_transform(data, period=10)
           f_val = fisher_df['fisher'].iloc[-1]
           f_sig = fisher_df['fisher_signal'].iloc[-1]
           if f_val > f_sig and f_val < -1.0:
               signals['buy'] += 2    # Bullish di zona oversold
           elif f_val < f_sig and f_val > 1.0:
               signals['sell'] += 2   # Bearish di zona overbought
           signals['total'] += 2
     
           # 2. Super Smoother trend direction
           ss = super_smoother(data['close'], period=20)
           if ss.iloc[-1] > ss.iloc[-3]: signals['buy'] += 1
           elif ss.iloc[-1] < ss.iloc[-3]: signals['sell'] += 1
           signals['total'] += 1
     
           # 3. MAMA/FAMA crossover (adaptive trend)
           mama_df = mama(data)
           if mama_df['MAMA'].iloc[-1] > mama_df['FAMA'].iloc[-1]:
               signals['buy'] += 1
           else:
               signals['sell'] += 1
           signals['total'] += 1
     
           # Hitung confidence berdasarkan agreement
           if signals['total'] == 0: return None
           buy_ratio = signals['buy'] / signals['total']
           sell_ratio = signals['sell'] / signals['total']
     
           if buy_ratio > sell_ratio:
               return SignalComponent(
                   source='ehlers', signal=SignalType.BUY,
                   confidence=50 + (buy_ratio * 40),
                   weight=self.weights.get('ehlers', 0.30),
                   details={'reason': f'Ehlers bullish ({signals["buy"]}/{signals["total"]})',
                            'fisher': f_val, 'fisher_signal': f_sig})
           elif sell_ratio > buy_ratio:
               return SignalComponent(
                   source='ehlers', signal=SignalType.SELL,
                   confidence=50 + (sell_ratio * 40),
                   weight=self.weights.get('ehlers', 0.30),
                   details={'reason': f'Ehlers bearish'})
           return None
     
       try:
           return await self._run_in_executor(_sync_analyze)
       except Exception as e:
           raise AnalysisError('ehlers', str(e), e)

    
    async def _analyze_ml(
        self,
        data: pd.DataFrame
    ) -> Optional[SignalComponent]:
        """Analyze using ML models (async)."""
        def _sync_analyze():
            # ML disabled - tidak ada model terlatih
            logger.debug('ML engine disabled: no trained model')
            return SignalComponent(
                source='ml',
                signal=SignalType.HOLD,
                confidence=0,
                weight=0,
                details={'reason': 'ML disabled - awaiting trained model'}
            )
        
        return await self._run_in_executor(_sync_analyze)
    
    async def _analyze_patterns(
        self,
        data: pd.DataFrame,
        symbol=None
    ) -> Optional[SignalComponent]:
        """Analyze chart patterns (async)."""
        def _sync_analyze():
            if len(data) < 20:
                return None
            
            from scanner.Candlestick_Pattern_Scanner import CandlestickPatternScanner
            scanner = CandlestickPatternScanner({})
            patterns = scanner.scan(data, symbol='')
            
            bullish_count = sum(1 for p in patterns 
                if p.type.value in ['bullish_reversal', 'bullish_continuation'])
            bearish_count = sum(1 for p in patterns 
                if p.type.value in ['bearish_reversal', 'bearish_continuation'])
            
            if bullish_count > bearish_count:
                best = max([p for p in patterns if 'bullish' in p.type.value],
                           key=lambda x: x.reliability.value, default=None)
                confidence = {'low': 50, 'medium': 60, 'high': 72, 'very_high': 85}
                return SignalComponent(
                    source='pattern', signal=SignalType.BUY,
                    confidence=confidence.get(best.reliability.value, 55),
                    weight=self.weights.get('pattern', 0.15),
                    details={'patterns': [p.name for p in patterns]})
        
        try:
            return await self._run_in_executor(_sync_analyze)
        except Exception as e:
            raise AnalysisError('pattern', str(e), e)
    
    def _extract_reasons(self, components: List[SignalComponent]) -> List[str]:
        """Extract reasons from high-confidence components."""
        reasons = []
        for comp in components:
            if comp.error is None and comp.confidence > 60:
                reason = f"{comp.source.capitalize()}: {comp.details.get('reason', 'Signal detected')}"
                reasons.append(reason)
        return reasons
    
    def _build_attribution(self, components: List[SignalComponent]) -> Dict[str, float]:
        """Build model attribution from components."""
        attribution = {}
        for c in components:
            if c.error is None and c.weight > 0:
                attribution[c.source] = c.weight * c.confidence
        
        total_attr = sum(attribution.values()) or 1
        return {k: round(v / total_attr * 100, 1) for k, v in attribution.items()}
    
    def _combine_signals(self, components: List[SignalComponent]) -> Tuple[SignalType, float, SignalStrength]:
        """Combine all signal components into final signal."""
        # Filter out failed components
        valid_components = [c for c in components if c.error is None and c.weight > 0]
        
        if not valid_components:
            return SignalType.HOLD, 50.0, SignalStrength.WEAK
        
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        for comp in valid_components:
            weight = comp.weight * (comp.confidence / 100)
            total_weight += comp.weight
            
            if comp.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                buy_score += weight
            elif comp.signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                sell_score += weight
        
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        if buy_score > sell_score and buy_score > 0.4:
            signal = SignalType.STRONG_BUY if buy_score > 0.7 else SignalType.BUY
            confidence = buy_score * 100
        elif sell_score > buy_score and sell_score > 0.4:
            signal = SignalType.STRONG_SELL if sell_score > 0.7 else SignalType.SELL
            confidence = sell_score * 100
        else:
            signal = SignalType.HOLD
            confidence = 50
        
        if confidence >= 80:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 65:
            strength = SignalStrength.STRONG
        elif confidence >= 50:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        return signal, min(95, confidence), strength
    
    def _calculate_levels(self, data: pd.DataFrame, signal: SignalType, current_price: float) -> Tuple[float, float, float]:
        """Calculate entry, stop loss, and take profit levels."""
        if len(data) < 20:
            if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                return current_price, current_price * 0.98, current_price * 1.04
            elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                return current_price, current_price * 1.02, current_price * 0.96
            return current_price, current_price, current_price
        
        # ATR calculation
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            entry = current_price
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 3)
        elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            entry = current_price
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 3)
        else:
            entry = current_price
            stop_loss = current_price
            take_profit = current_price
        
        return round(entry, 4), round(stop_loss, 4), round(take_profit, 4)
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float, signal: SignalType) -> float:
        """Calculate risk-reward ratio."""
        if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
        elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            risk = abs(stop_loss - entry)
            reward = abs(entry - take_profit)
        else:
            return 0.0
        
        return reward / risk if risk > 0 else 0.0
    
    async def update_weights(self, weights: Dict[str, float]):
        """Update component weights (thread-safe)."""
        async with self._cache_lock:
            self.weights.update(weights)
    
    async def get_signal_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get signal history (thread-safe)."""
        async with self._history_lock:
            history = self.signal_history.copy()
        
        if symbol:
            history = [s for s in history if s.symbol == symbol]
        return [s.to_dict() for s in history[-limit:]]
    
    async def generate_signals(
        self,
        data: pd.DataFrame,
        gann_levels: Dict = None,
        astro_events: List = None,
        symbol: str = 'UNKNOWN',
        timeframe: str = "H1"
    ) -> pd.DataFrame:
        """
        Legacy compatibility wrapper for API endpoints (async).
        Converts the new AISignal format to DataFrame format expected by backtester.
        
        Args:
            data: OHLCV DataFrame
            gann_levels: Optional Gann price levels (ignored, calculated internally)
            astro_events: Optional astro events (ignored, calculated internally)
            symbol: Trading symbol
            timeframe: Timeframe of the data
            
        Returns:
            DataFrame with signal data for backtesting
        """
        # Generate the AI signal
        signal = await self.generate_signal(
            symbol=symbol,
            data=data,
            timeframe=timeframe
        )
        
        # Convert AISignal to DataFrame format expected by backtester
        return pd.DataFrame([{
            'timestamp': signal.timestamp,
            'signal': signal.signal.value,
            'price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'confidence': signal.confidence,
            'strength': signal.strength.name,
            'reason': ', '.join(signal.reasons) if signal.reasons else '',
            'risk_reward': signal.risk_reward
        }])
    
    async def cleanup(self):
        """Cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("AISignalEngine cleanup completed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Singleton instance
_signal_engine: Optional[AISignalEngine] = None
_engine_lock = asyncio.Lock()


async def get_signal_engine(config: Dict = None) -> AISignalEngine:
    """Get or create the signal engine (thread-safe async)."""
    global _signal_engine
    
    async with _engine_lock:
        if _signal_engine is None:
            _signal_engine = AISignalEngine(config)
        return _signal_engine


# Synchronous wrapper for backward compatibility
def get_signal_engine_sync(config: Dict = None) -> AISignalEngine:
    """Synchronous wrapper for backward compatibility."""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = AISignalEngine(config)
    return _signal_engine


# Convenience function for running async signal generation
def run_async_signal(
    symbol: str,
    data: pd.DataFrame,
    timeframe: str = "H1",
    current_price: float = None,
    config: Dict = None
) -> AISignal:
    """
    Convenience function to run async signal generation from synchronous code.
    
    Usage:
        signal = run_async_signal("EURUSD", df, "H1", 1.0500)
    """
    async def _run():
        engine = await get_signal_engine(config)
        return await engine.generate_signal(symbol, data, timeframe, current_price)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run())
                return future.result()
        else:
            return loop.run_until_complete(_run())
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(_run())
