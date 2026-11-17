"""Run a daily scan and send Telegram alerts for qualifying candidates.
Schedule after the US market close. Example: python scanner.py
"""
import pandas as pd
from pathlib import Path
from momentum_radar.data import load_universe, fetch_history
from momentum_radar.signals import score_symbol
from momentum_radar.alerts import send_telegram

symbols = load_universe(Path("universe.csv"))
rows = []
for ticker in symbols:
    try:
        signal = score_symbol(ticker, fetch_history(ticker, "1y", "1d"))
        if signal and signal["score"] >= 75:
            rows.append(signal)
    except Exception as exc:
        print(f"Skipped {ticker}: {exc}")
if rows:
    rows = sorted(rows, key=lambda x: x["score"], reverse=True)
    pd.DataFrame(rows).to_csv("latest_signals.csv", index=False)
    for row in rows[:10]:
        print(row)
        send_telegram(row)
else:
    print("No qualifying signals.")
