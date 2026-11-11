def size_position(capital, risk_pct, entry, stop, max_allocation_pct=0.25):
    risk_per_share = max(entry - stop, 0)
    risk_budget = capital * risk_pct
    if risk_per_share <= 0 or entry <= 0:
        shares = 0
    else:
        by_risk = int(risk_budget // risk_per_share)
        by_allocation = int((capital * max_allocation_pct) // entry)
        shares = max(0, min(by_risk, by_allocation))
    value = shares * entry
    return {
        "shares": shares,
        "position_value": round(value, 2),
        "planned_risk": round(shares * risk_per_share, 2),
        "risk_budget": round(risk_budget, 2)
    }
