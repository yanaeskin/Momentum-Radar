import numpy as np
import pandas as pd

def enrich(df):
    x = df.copy()
    close, high, low, volume = x.Close, x.High, x.Low, x.Volume
    x["sma20"] = close.rolling(20).mean()
    x["sma50"] = close.rolling(50).mean()
    x["vol20"] = volume.rolling(20).mean()
    x["dollar_vol20"] = (close * volume).rolling(20).mean()
    x["rvol"] = volume / x.vol20.replace(0, np.nan)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["rsi"] = 100 - (100 / (1 + rs))
    prev_close = close.shift()
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean()
    x["high20_prev"] = high.shift(1).rolling(20).max()
    x["ret20"] = close.pct_change(20)
    return x

def score_symbol(symbol, df, min_price=5, min_dollar_volume_m=20, min_rvol=1.8):
    x = enrich(df).dropna()
    if x.empty:
        return None
    r = x.iloc[-1]
    if r.Close < min_price or r.dollar_vol20 < min_dollar_volume_m * 1_000_000:
        return None
    trend = r.Close > r.sma20 > r.sma50
    breakout = r.Close > r.high20_prev
    volume_ok = r.rvol >= min_rvol
    rsi_ok = 50 <= r.rsi <= 78
    relative = r.ret20 > 0
    score = 0
    score += 25 if trend else 0
    score += 20 if relative else 0
    score += 20 if volume_ok else 0
    score += 25 if breakout else 0
    score += 10 if rsi_ok else 0
    if score < 60:
        return None
    stop = max(float(r.Close - 2 * r.atr), 0.01)
    return {
        "symbol": symbol, "score": int(score), "price": round(float(r.Close), 2),
        "stop": round(stop, 2), "rsi14": round(float(r.rsi), 1),
        "rvol": round(float(r.rvol), 2), "return_20d_pct": round(float(r.ret20*100), 2),
        "dollar_volume_20d_m": round(float(r.dollar_vol20/1e6), 1),
        "trend": bool(trend), "breakout": bool(breakout),
        "volume_confirmed": bool(volume_ok)
    }
