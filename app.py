import streamlit as st
import pandas as pd
from pathlib import Path
from momentum_radar.data import load_universe, fetch_history, discover_us_common_stocks
from momentum_radar.signals import score_symbol
from momentum_radar.risk import size_position
from momentum_radar.backtest import run_backtest
from momentum_radar.alerts import send_telegram

st.set_page_config(page_title="Momentum Radar", page_icon="📡", layout="wide")
st.title("📡 Momentum Radar")
st.caption("US equities · Short-term momentum · Paper trading only")
st.warning("Research prototype only. The universe is discovered from Nasdaq Trader symbol directories, but price data comes from Yahoo Finance and may be delayed, incomplete or rate-limited. This is not an all-market real-time scanner or trading system.")

with st.sidebar:
    st.header("Settings")
    capital = st.number_input("Virtual capital ($)", min_value=100.0, value=1000.0, step=100.0)
    risk_pct = st.slider("Risk per trade (%)", 0.25, 2.0, 1.0, 0.25) / 100
    min_price = st.number_input("Minimum price ($)", min_value=1.0, value=5.0)
    min_dollar_volume = st.number_input("Minimum average daily dollar volume ($M)", min_value=1.0, value=20.0)
    min_rvol = st.number_input("Minimum relative volume", min_value=1.0, value=1.8, step=0.1)
    scan_limit = st.select_slider("Maximum symbols per scan", options=[100, 250, 500, 1000], value=250)
    st.caption("A full listing directory can contain thousands of symbols. Scan in batches to reduce Yahoo Finance rate limits.")

st.subheader("US stock universe")
left, right = st.columns([1, 2])
with left:
    if st.button("🌎 Refresh US listings", type="primary", use_container_width=True):
        try:
            listing = discover_us_common_stocks()
            st.session_state["dynamic_universe"] = listing
            st.success(f"Loaded {len(listing):,} listed common-stock symbols.")
        except Exception as e:
            st.error(f"Could not refresh listings: {e}")
with right:
    st.caption("Refresh downloads the current Nasdaq Trader symbol directories and excludes ETFs/test issues. It does not guarantee every security is a common stock or has usable Yahoo Finance history.")

if "dynamic_universe" in st.session_state:
    universe_df = st.session_state["dynamic_universe"]
    symbols = universe_df["symbol"].tolist()
    st.write(f"Discovered listing universe: **{len(symbols):,} symbols**")
    st.dataframe(universe_df.head(12), use_container_width=True, hide_index=True)
else:
    symbols = load_universe(Path("universe.csv"))
    st.info(f"Using starter watchlist: {len(symbols)} symbols. Click **Refresh US listings** to discover the broader US listing universe.")

st.write(f"Symbols selected for this scan: **{min(len(symbols), int(scan_limit)):,}**")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔎 Scan market", type="primary", use_container_width=True):
        rows, errors = [], []
        selected = symbols[:int(scan_limit)]
        progress = st.progress(0)
        status = st.empty()
        for i, ticker in enumerate(selected):
            try:
                hist = fetch_history(ticker, period="1y", interval="1d")
                signal = score_symbol(ticker, hist, min_price=min_price,
                                      min_dollar_volume_m=min_dollar_volume,
                                      min_rvol=min_rvol)
                if signal:
                    rows.append(signal)
            except Exception as e:
                errors.append(f"{ticker}: {e}")
            progress.progress((i + 1) / max(1, len(selected)))
            if (i + 1) % 25 == 0:
                status.caption(f"Scanned {i+1:,}/{len(selected):,} symbols · candidates: {len(rows)}")
        if rows:
            result = pd.DataFrame(rows).sort_values("score", ascending=False)
            st.session_state["scan_results"] = result
            st.success(f"Scan complete: {len(result)} candidates from {len(selected)} symbols.")
        else:
            st.session_state["scan_results"] = pd.DataFrame()
            st.info("No qualifying signals found. That is a valid result; do not loosen filters just to force trades.")
        st.session_state["scan_error_count"] = len(errors)
        if errors:
            st.caption(f"{len(errors)} symbols returned data errors (missing history, invalid ticker, rate limits, etc.).")
with col2:
    if st.button("📨 Send top signal to Telegram", use_container_width=True):
        data = st.session_state.get("scan_results", pd.DataFrame())
        if data.empty:
            st.info("Run a scan first.")
        else:
            sent = send_telegram(data.iloc[0].to_dict())
            st.success("Telegram message sent." if sent else "Telegram not configured or message failed.")

st.subheader("Market opportunities")
results = st.session_state.get("scan_results", pd.DataFrame())
if not results.empty:
    st.dataframe(results, use_container_width=True, hide_index=True)
    chosen = st.selectbox("Select a candidate for position sizing", results["symbol"].tolist())
    row = results.loc[results.symbol == chosen].iloc[0]
    plan = size_position(capital, risk_pct, float(row.price), float(row.stop), max_allocation_pct=0.25)
    a, b, c, d = st.columns(4)
    a.metric("Entry reference", f"${row.price:.2f}")
    b.metric("Stop reference", f"${row.stop:.2f}")
    c.metric("Risk budget", f"${capital*risk_pct:.2f}")
    d.metric("Shares (whole)", str(plan["shares"]))
    st.caption(f"Estimated position: ${plan['position_value']:.2f} · Planned risk: ${plan['planned_risk']:.2f}. Limit per position: 25% of virtual capital.")
else:
    st.info("No scan results yet.")

st.divider()
st.subheader("Backtest")
bt_symbol = st.text_input("Ticker to backtest", value="VRT").upper().strip()
if st.button("Run historical backtest"):
    try:
        hist = fetch_history(bt_symbol, period="5y", interval="1d")
        report, trades, equity = run_backtest(hist, initial_capital=capital, risk_pct=risk_pct)
        st.session_state["bt_report"] = report
        st.session_state["bt_trades"] = trades
        st.session_state["bt_equity"] = equity
    except Exception as e:
        st.error(f"Backtest failed: {e}")
if "bt_report" in st.session_state:
    st.json(st.session_state["bt_report"])
    st.line_chart(st.session_state["bt_equity"].set_index("date")["equity"])
    st.dataframe(st.session_state["bt_trades"], use_container_width=True, hide_index=True)

st.divider()
st.caption("No brokerage connection. No orders are sent to Meitav or any broker. Backtest results are hypothetical and do not predict future performance.")
