# Momentum Radar

A Streamlit research prototype for short-term momentum scanning of US-listed equities. Paper trading only; it does not connect to a broker or place orders.

## What's new
- Refreshes a broad US listing universe from Nasdaq Trader symbol-directory files (`nasdaqtraded.txt` and `otherlisted.txt`).
- Excludes securities marked as ETFs or test issues in those directories.
- Lets the user scan a capped batch (100/250/500/1000 symbols) to reduce free-data rate limits.
- Retains momentum scoring, ATR-based stop reference, position sizing, backtesting and optional Telegram alert.

## Important limitations
- The symbol directory is a listing universe, not a curated list of only common operating-company stocks. Some unusual security types may remain; some symbols may not have Yahoo Finance data.
- Yahoo Finance/yfinance is an unofficial data source. Data may be delayed, incomplete, throttled, adjusted, or unavailable. This is not a reliable real-time scanner.
- The app scans only the first N symbols in the sorted directory per run, not the entire market simultaneously. For genuinely broad and repeatable coverage, use a licensed market-data provider and a dedicated background worker.
- The first batch is alphabetically ordered, so repeated 100/250-symbol scans are biased toward earlier symbols. Increase the scan cap or later add rotating/randomized batches before interpreting results as market-wide.
- Signals are educational heuristics, not investment advice. Backtests are simplified and may omit slippage, commissions, survivorship bias and other real-world effects.

## Deploy on Streamlit Community Cloud
- Repository root must contain `app.py`, `requirements.txt`, `universe.csv`, `scanner.py`, and the `momentum_radar/` folder.
- Main file path: `app.py`.
- Do not commit `.env` or bot credentials. Configure secrets through Streamlit app settings if Telegram is used.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```
