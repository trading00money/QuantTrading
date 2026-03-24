import yfinance as yf
from scanner.Candlestick_Pattern_Scanner import CandlestickPatternScanner

df = yf.download('BTC-USD', interval='1d', period='6mo')

df = df.tail(100)

# 🔥 FIX MultiIndex + lowercase
df.columns = df.columns.get_level_values(0).str.lower()

scanner = CandlestickPatternScanner({})

patterns = scanner.scan(df, symbol='BTC')

print(f'Total patterns: {len(patterns)}')
print("RAW patterns:", patterns)
print(df[['open','high','low','close']].tail(10))

for p in patterns:
    print(p.name, p.type, p.reliability.value)