import pandas as pd
import yaml
import os

# ==============================
# LOAD YAML (AUTO PATH)
# ==============================
BASE_DIR = os.path.dirname(__file__)

file_path = os.path.join(
    BASE_DIR,
    'config',
    'Candlestick_Pattern.yaml'
)

print("File path:", file_path)
print("Exists:", os.path.exists(file_path))

with open(file_path, 'r') as f:
    config = yaml.safe_load(f)

patterns = config['patterns']
print(f"\nTotal patterns loaded: {len(patterns)}")


# ==============================
# TEST DATA (FORCED PATTERN)
# ==============================
df = pd.DataFrame([
    {'open': 100, 'high': 105, 'low': 95, 'close': 96},   # bearish
    {'open': 95,  'high': 110, 'low': 94, 'close': 108},  # bullish engulfing
])

# ==============================
# HELPER FUNCTIONS
# ==============================
def analyze_candle(c):
    body = abs(c['close'] - c['open'])
    range_ = c['high'] - c['low']
    body_ratio = body / range_ if range_ != 0 else 0

    return {
        'body_ratio': body_ratio,
        'is_bullish': c['close'] > c['open'],
        'is_bearish': c['close'] < c['open'],
        'open': c['open'],
        'close': c['close'],
        'high': c['high'],
        'low': c['low']
    }


def detect_trend(df):
    if len(df) < 5:
        return "neutral"
    return "up" if df['close'].iloc[-1] > df['close'].iloc[-5] else "down"


# ==============================
# PREPARE DATA
# ==============================
c1 = analyze_candle(df.iloc[-2])
c2 = analyze_candle(df.iloc[-1])
trend = detect_trend(df)

print("\nTrend:", trend)
print("C1:", c1)
print("C2:", c2)


# ==============================
# RULE CHECKER
# ==============================
def check_rule(rule, c1, c2, trend):
    if not isinstance(rule, dict):
        return True

    for key, val in rule.items():

        # ----------------------
        # BODY RATIO
        # ----------------------
        if key == 'body_ratio':
            val = val.strip()
            if '>' in val:
                threshold = float(val.replace('>', '').strip())
                if not (c2['body_ratio'] > threshold):
                    return False
            elif '<' in val:
                threshold = float(val.replace('<', '').strip())
                if not (c2['body_ratio'] < threshold):
                    return False

        # ----------------------
        # TREND
        # ----------------------
        elif key == 'trend':
            if trend != val:
                return False

        # ----------------------
        # C1 / C2 BASIC
        # ----------------------
        elif key == 'c1':
            if 'bearish' in val and not c1['is_bearish']:
                return False
            if 'bullish' in val and not c1['is_bullish']:
                return False

        elif key == 'c2':
            if 'bullish' in val and not c2['is_bullish']:
                return False
            if 'bearish' in val and not c2['is_bearish']:
                return False

            # engulfing logic
            if 'engulfs' in val:
                if not (
                    c2['open'] < c1['close'] and
                    c2['close'] > c1['open']
                ):
                    return False

    return True


# ==============================
# MAIN TEST LOOP
# ==============================
matches = []

for p in patterns:
    rules = p.get('rules', [])
    passed = True

    for r in rules:
        if not check_rule(r, c1, c2, trend):
            passed = False
            break

    if passed:
        matches.append(p['name'])

# ==============================
# OUTPUT
# ==============================
print("\nMATCHES:")
if matches:
    for m in matches:
        print("-", m)
else:
    print("No patterns matched ❌")