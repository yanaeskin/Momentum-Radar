# Momentum Radar MVP

A research and paper-trading prototype for US equity short-term momentum.
It does **not** connect to Meitav, place orders, or provide guaranteed real-time quotes.

## What is included
- Daily-bar stock scanner (symbols supplied in `universe.csv`)
- Momentum score: trend, 20-day relative performance, relative volume, 20-day breakout, RSI
- ATR-based indicative stop and position sizing
- Daily-bar historical backtest with next-session-open entries, stop/target logic, fees/slippage hooks
- Streamlit dashboard
- Optional Telegram alerts
- $1,000 virtual capital default and 1% risk setting

## Important data limitations
This MVP uses Yahoo Finance through `yfinance`. It is suitable for prototyping and historical exploration, **not** a dependable real-time consolidated US market feed. Coverage, delays, intervals, corporate-action adjustments and rate limits may vary. The default universe is a small starter list, not all US-listed equities. Expand `universe.csv` using a properly licensed symbol master before claiming full-market coverage.

Telegram delivers phone notifications when the bot is configured. Streamlit itself does not run as a background service; deploy the app and schedule `scanner.py` on an always-on host to get recurring alerts. Free hosting may sleep or have execution limits. No native iOS push service is included.

## Install
Python 3.10+ recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run dashboard
```bash
streamlit run app.py
```

## Telegram setup
1. Create a bot using Telegram's official BotFather.
2. Start a chat with your bot and obtain your chat ID.
3. Copy `.env.example` to `.env` and fill in the values.
4. Load variables before running, for example:
   ```bash
   export $(grep -v '^#' .env | xargs)
   python scanner.py
   ```
   On Windows, set environment variables in PowerShell instead.

Never share the bot token or commit `.env`.

## Scheduling
Run `python scanner.py` once after the US market close on each trading day using cron / Task Scheduler / an always-on host. Hourly scans are not recommended with this free data source.

## Strategy specification (v1)
- Close > SMA20 > SMA50
- Close > prior 20-session high
- Relative volume >= 1.8
- RSI(14) in [50, 78]
- 20-session average dollar volume >= $20m
- Score >= 60 for watchlist; >= 75 for Telegram alert
- Indicative stop = signal close - 2*ATR(14)
- Backtest: signal on close, entry next session open, 2R target, 15-session time exit
- Conservative intrabar assumption: if stop and target are both touched on the same daily bar, stop is assumed first
- Position risk budget = 1% of virtual equity; max position allocation = 25%

## Validation before real money
1. Expand universe with survivorship-bias-aware historical symbols.
2. Add split/dividend and delisting handling checks.
3. Run out-of-sample and walk-forward tests.
4. Compare against buy-and-hold and simple momentum benchmarks.
5. Include realistic spreads, fees, slippage and rejected/missed alerts.
6. Paper trade for at least 8-12 weeks; review expectancy and drawdown.
7. Do not infer an edge from a small sample.

## Known MVP limitations / fixes for next iteration
- No true real-time SIP stream.
- No alert deduplication database yet; repeated scans can repeat alerts.
- No portfolio correlation / sector exposure model.
- Backtest is single-position, long-only, daily-bar and simplified.
- No survivorship-bias-free full-market universe.
- The scanner may hit Yahoo rate limits on large universes.
