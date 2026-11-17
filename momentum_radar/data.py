import pandas as pd
import yfinance as yf
from pathlib import Path

def load_universe(path: Path):
    if not path.exists():
        return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "VRT", "ETN", "MOD", "ANET", "AMD"]
    df = pd.read_csv(path)
    col = "symbol" if "symbol" in df.columns else df.columns[0]
    return sorted(set(df[col].dropna().astype(str).str.upper().str.strip()))

def fetch_history(symbol, period="1y", interval="1d"):
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
    if df is None or df.empty:
        raise ValueError("No price history returned")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.title)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    df = df[[c for c in needed if c in df.columns]].dropna()
    if len(df) < 60:
        raise ValueError("Not enough history (need at least 60 daily bars)")
    return df
