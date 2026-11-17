import io
from pathlib import Path
import pandas as pd
import requests
import yfinance as yf

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def _read_pipe(url):
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 MomentumRadar/1.0"})
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), sep="|", dtype=str)
    # Nasdaq symbol-directory files end with a footer row.
    if len(df.columns):
        first = df.columns[0]
        df = df[df[first].notna() & (df[first].str.upper() != "FILE CREATION TIME")]
    return df


def discover_us_common_stocks():
    """Discover listed US common-stock symbols from Nasdaq Trader symbol directories.
    ETFs and test issues are excluded. This is a listing universe, not a real-time screener.
    """
    nas = _read_pipe(NASDAQ_URL)
    oth = _read_pipe(OTHER_URL)
    frames = []
    if {"Symbol", "ETF", "Test Issue"}.issubset(nas.columns):
        a = nas[(nas["ETF"] == "N") & (nas["Test Issue"] == "N")].copy()
        frames.append(a[["Symbol", "Security Name"]])
    if {"ACT Symbol", "ETF", "Test Issue"}.issubset(oth.columns):
        b = oth[(oth["ETF"] == "N") & (oth["Test Issue"] == "N")].copy()
        b = b.rename(columns={"ACT Symbol": "Symbol"})
        frames.append(b[["Symbol", "Security Name"]])
    if not frames:
        raise RuntimeError("Unexpected Nasdaq Trader symbol-directory format")
    out = pd.concat(frames, ignore_index=True).dropna(subset=["Symbol"])
    out["symbol"] = out["Symbol"].str.strip().str.replace(".", "-", regex=False)
    out["name"] = out["Security Name"].fillna("").str.strip()
    out = out[out["symbol"].str.fullmatch(r"[A-Z][A-Z0-9-]{0,9}", na=False)]
    out = out.drop_duplicates("symbol").sort_values("symbol")
    return out[["symbol", "name"]].reset_index(drop=True)


def load_universe(path: Path):
    if not path.exists():
        return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "VRT", "ETN", "AMD"]
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
