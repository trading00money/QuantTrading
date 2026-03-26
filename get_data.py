import yfinance as yf

data = yf.download("BTC/USDT", interval="1h", period="180d")

data = data[['Open','High','Low','Close']]
data.columns = ['open','high','low','close']

data.to_csv("data.csv")

print("DONE")