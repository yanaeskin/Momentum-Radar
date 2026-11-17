import pandas as pd
from .signals import enrich

def run_backtest(df, initial_capital=1000, risk_pct=0.01, fee_per_order=0.0, slippage_bps=5):
    """
    Daily-bar breakout simulation:
    signal at close; enter next day's open (no same-bar look-ahead).
    Initial stop = signal close - 2*ATR; target = 2R.
    Conservative rule: if stop and target both touched in one bar, assume stop first.
    One position at a time; max 15 trading days.
    """
    x = enrich(df).dropna().copy()
    cash = float(initial_capital)
    equity_rows, trades = [], []
    i = 0
    while i < len(x) - 2:
        r = x.iloc[i]
        signal = (r.Close > r.sma20 > r.sma50 and r.Close > r.high20_prev
                  and r.rvol >= 1.8 and 50 <= r.rsi <= 78 and r.dollar_vol20 >= 20_000_000)
        if not signal:
            equity_rows.append({"date": x.index[i], "equity": cash})
            i += 1
            continue
        entry_i = i + 1
        entry_raw = float(x.iloc[entry_i].Open)
        entry = entry_raw * (1 + slippage_bps / 10000)
        stop = max(float(r.Close - 2*r.atr), 0.01)
        risk_ps = entry - stop
        if risk_ps <= 0:
            i += 1
            continue
        risk_budget = cash * risk_pct
        shares = min(int(risk_budget // risk_ps), int((cash * 0.25) // entry))
        if shares < 1:
            equity_rows.append({"date": x.index[i], "equity": cash})
            i += 1
            continue
        target = entry + 2*risk_ps
        exit_price, exit_date, reason, exit_i = None, None, None, None
        for j in range(entry_i, min(entry_i + 15, len(x))):
            bar = x.iloc[j]
            stop_hit, target_hit = float(bar.Low) <= stop, float(bar.High) >= target
            if stop_hit:
                exit_price, exit_date, reason, exit_i = stop*(1-slippage_bps/10000), x.index[j], "stop", j
                break
            if target_hit:
                exit_price, exit_date, reason, exit_i = target*(1-slippage_bps/10000), x.index[j], "target", j
                break
        if exit_price is None:
            exit_i = min(entry_i + 14, len(x)-1)
            exit_price = float(x.iloc[exit_i].Close)*(1-slippage_bps/10000)
            exit_date, reason = x.index[exit_i], "time_exit"
        pnl = shares*(exit_price-entry) - 2*fee_per_order
        cash += pnl
        trades.append({"entry_date": x.index[entry_i], "exit_date": exit_date, "entry": round(entry,2),
                       "exit": round(exit_price,2), "shares": shares, "pnl": round(pnl,2), "reason": reason})
        equity_rows.append({"date": exit_date, "equity": cash})
        i = exit_i + 1
    if not equity_rows:
        equity_rows = [{"date": x.index[-1], "equity": cash}]
    eq = pd.DataFrame(equity_rows).drop_duplicates("date").sort_values("date")
    t = pd.DataFrame(trades)
    wins = int((t.pnl > 0).sum()) if not t.empty else 0
    gross_profit = float(t.loc[t.pnl > 0, "pnl"].sum()) if not t.empty else 0
    gross_loss = abs(float(t.loc[t.pnl < 0, "pnl"].sum())) if not t.empty else 0
    peak = eq.equity.cummax()
    dd = (eq.equity / peak - 1).min()
    report = {
        "trades": int(len(t)), "win_rate_pct": round(wins/len(t)*100, 1) if len(t) else 0,
        "net_pnl": round(cash-initial_capital, 2),
        "return_pct": round((cash/initial_capital-1)*100, 2),
        "profit_factor": round(gross_profit/gross_loss, 2) if gross_loss else None,
        "max_drawdown_pct": round(float(dd)*100, 2),
        "note": "Hypothetical daily-bar test; excludes taxes, borrow costs and market impact. Not predictive."
    }
    return report, t, eq
