"""Sharpe ratios under a non-zero constant risk-free rate.

The manuscript reports Sharpe ratios at a zero risk-free rate. Every strategy in
the study is fully invested, so the same constant rate is subtracted from every
strategy's mean return; the ranking can still change, because the strategies
differ in volatility and a fixed subtraction penalizes low-volatility strategies
more. This script recomputes the Sharpe ratios at 0, 2 and 4 percent per annum
from the archived holding-period returns.

This is a constant-rate sensitivity, not a Treasury-bill excess-return study: it
answers whether the reported ordering survives a non-zero rate, not what the
realized excess returns were.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HERE, "..", "results"))

TEX_NAME = {"1/N_Ret": "1/N", "MinVar_Ret": "TC-MinVar",
            "NominalCVaR_Ret": "Nominal CVaR",
            "FiniteRegime_Ret": "Finite-Regime CVaR",
            "RobustSIP_Ret": "Robust SIP"}
RATES = [0.00, 0.02, 0.04]


def main():
    d = pd.read_csv(os.path.join(RESULTS, "strategy_holding_period_returns.csv"))
    rows = []
    for col, name in TEX_NAME.items():
        r = d[col].dropna().values
        ann_vol = r.std(ddof=1) * np.sqrt(12.0)
        rec = {"Strategy": name, "Ann_Return": r.mean() * 12.0, "Ann_Vol": ann_vol}
        for rf in RATES:
            rec[f"Sharpe_rf{int(rf * 100)}"] = (r.mean() * 12.0 - rf) / ann_vol
        rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RESULTS, "riskfree_sensitivity.csv"), index=False)
    print(out.round(4).to_string(index=False))

    ranks = {rf: list(out.sort_values(f"Sharpe_rf{int(rf * 100)}",
                                      ascending=False).Strategy) for rf in RATES}
    same = all(ranks[rf] == ranks[0.0] for rf in RATES)
    print("\nranking preserved across all rates:", same)


if __name__ == "__main__":
    main()
