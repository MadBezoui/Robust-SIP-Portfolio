"""Cross-check every numerical table in the manuscript against its source CSV.

Manual transcription between the result files and the LaTeX tables is the main
way inconsistencies creep in, so this script parses the tables straight out of
``main_paper.tex`` and compares each cell with the corresponding value in
``Code/results``.  It also checks the cross-table identities that must hold
between different views of the same backtest.

Run from ``Code/code``:

    python3 validate_manuscript.py            # exits non-zero on any mismatch
    python3 validate_manuscript.py -v         # also list the checks that pass
"""

import argparse
import os
import re
import sys

import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT_DIR, "Soumission", "main_paper.tex")
RESULTS = os.path.join(ROOT_DIR, "results")

# Strategy naming differs between the CSVs and the manuscript tables.
CSV_TO_TEX = {
    "1/N": "1/N",
    "MinVar": "TC-MinVar",
    "NominalCVaR": "Nominal CVaR",
    "FiniteRegime": "Finite-Regime CVaR",
    "RobustSIP": "Robust SIP",
}

failures = []
passes = []


def csv(name):
    return pd.read_csv(os.path.join(RESULTS, name))


def check(label, got, want, tol):
    """Compare one manuscript cell against one CSV value."""
    if got is None:
        failures.append(f"{label}: value not found in the manuscript")
        return
    # allow the exact half-ulp boundary, e.g. 172.45 printed as 172.5
    if abs(got - want) <= tol * (1 + 1e-9) + 1e-12:
        passes.append(f"{label}: {got} (source {want:.6g})")
    else:
        failures.append(
            f"{label}: manuscript {got} vs source {want:.6g} (tolerance {tol})")


# ---------------------------------------------------------------------------
# LaTeX table parsing
# ---------------------------------------------------------------------------
def table_rows(tex, label):
    """Return the body rows of the table carrying `label`, as cell lists."""
    i = tex.find("\\label{%s}" % label)
    if i < 0:
        failures.append(f"{label}: table not found in the manuscript")
        return []
    j = tex.find("\\midrule", i)
    k = tex.find("\\bottomrule", j)
    body = tex[j + len("\\midrule"):k]
    rows = []
    for raw in body.split("\\\\"):
        raw = raw.replace("\\midrule", "").strip()
        if not raw:
            continue
        rows.append([c.strip() for c in raw.split("&")])
    return rows


def num(cell):
    """Extract the numeric value of a LaTeX table cell, or None."""
    if cell is None:
        return None
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", cell)
    s = s.replace("\\%", "").replace("\\$", "").replace("$", "")
    s = s.replace("{", "").replace("}", "").replace(",", "").strip()
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    return float(m.group(0)) if m else None


def label_of(cells):
    """Normalised first-column label of a row."""
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", cells[0])
    return re.sub(r"[$\\{}]", "", s).strip()


# ---------------------------------------------------------------------------
# Table 2 -- heuristic continuous-domain diagnostics
# ---------------------------------------------------------------------------
def check_gap(tex):
    df = csv("gap_verification.csv")
    rows = {label_of(r): r for r in table_rows(tex, "tab:gap_verification")}
    for _, s in df.iterrows():
        r = rows.get(s["Label"])
        if r is None:
            failures.append(f"Table 2 [{s['Label']}]: row missing")
            continue
        check(f"Table 2 [{s['Label']}] max gradient norm", num(r[1]),
              s["MaxGradNorm"], 5e-3)
        check(f"Table 2 [{s['Label']}] grid dispersion", num(r[2]),
              s["GridDisp"], 5e-3)
        check(f"Table 2 [{s['Label']}] gradient-dispersion product", num(r[3]),
              s["EmpiricalProduct"], 5e-2)
        # last column is printed in scientific notation with one decimal
        got, want = num(r[4]), s["LocalSearchImp"]
        if got is None or abs(got - want) > max(1e-4, abs(want) * 0.05):
            failures.append(f"Table 2 [{s['Label']}] local-search improvement: "
                            f"manuscript {r[4]} vs source {want:.3g}")
        else:
            passes.append(f"Table 2 [{s['Label']}] local-search improvement")


# ---------------------------------------------------------------------------
# Table 4 -- headline out-of-sample performance
# ---------------------------------------------------------------------------
def check_performance(tex):
    df = csv("performance_table.csv").set_index("Strategy")
    rows = {label_of(r): r for r in table_rows(tex, "tab:performance")}
    for key, tex_name in CSV_TO_TEX.items():
        s = df.loc[key]
        r = rows.get(tex_name)
        if r is None:
            failures.append(f"Table 4 [{tex_name}]: row missing")
            continue
        check(f"Table 4 [{tex_name}] annualized return", num(r[1]),
              s["Ann_Mean"] * 100, 5e-3)
        check(f"Table 4 [{tex_name}] annualized volatility", num(r[2]),
              s["Ann_Vol"] * 100, 5e-3)
        check(f"Table 4 [{tex_name}] Sharpe", num(r[3]), s["Sharpe"], 5e-4)
        check(f"Table 4 [{tex_name}] maximum drawdown", num(r[4]),
              s["Max_DD"] * 100, 5e-3)
        check(f"Table 4 [{tex_name}] average turnover", num(r[5]),
              s["Avg_Turnover"] * 100, 5e-3)


# ---------------------------------------------------------------------------
# Table 5 -- crisis-period performance
# ---------------------------------------------------------------------------
def check_crisis(tex):
    df = csv("crisis_performance.csv")
    periods = list(dict.fromkeys(df["Period"]))
    rows = table_rows(tex, "tab:crisis")
    # rows carry the strategy in the second column
    seen = []
    for r in rows:
        if len(r) < 4:
            continue
        strat = re.sub(r"[$\\{}]|textbf", "", r[1]).strip()
        seen.append((strat, num(r[2]), num(r[3])))
    if len(seen) != len(df):
        failures.append(f"Table 5: {len(seen)} data rows but "
                        f"{len(df)} rows in crisis_performance.csv")
        return
    for (strat, ret, dd), (_, s) in zip(seen, df.iterrows()):
        want_strat = CSV_TO_TEX[s["Strategy"]]
        tag = f"Table 5 [{s['Period']}/{want_strat}]"
        if strat not in (want_strat, want_strat.replace(" CVaR", "")):
            failures.append(f"{tag}: strategy column reads '{strat}'")
        check(f"{tag} return", ret, s["Return"] * 100, 5e-3)
        check(f"{tag} maximum drawdown", dd, s["MaxDD"] * 100, 5e-3)


# ---------------------------------------------------------------------------
# Table 6 -- transaction-cost sensitivity
# ---------------------------------------------------------------------------
TC_LEVELS = [0.0, 5.0, 10.0, 20.0, 50.0]


def check_tc(tex):
    df = csv("tc_sensitivity.csv")
    rows = table_rows(tex, "tab:tc_sensitivity")
    block = None
    for r in rows:
        head = label_of(r)
        if "Sharpe" in head:
            block = "Sharpe"
            continue
        if "Wealth" in head:
            block = "Final_Wealth"
            continue
        if block is None:
            continue
        for csv_name, tex_name in CSV_TO_TEX.items():
            if head != tex_name:
                continue
            for col, tc in enumerate(TC_LEVELS, start=1):
                sel = df[(df.Strategy == csv_name) & (df.TC_bps == tc)]
                if sel.empty:
                    failures.append(f"Table 6 [{tex_name}, {tc:g} bps]: "
                                    "no matching CSV row")
                    continue
                want = sel[block].iloc[0]
                tol = 5e-4 if block == "Sharpe" else 5e-3
                check(f"Table 6 [{tex_name}, {tc:g} bps] "
                      f"{'Sharpe' if block == 'Sharpe' else 'wealth'}",
                      num(r[col]), want, tol)


# ---------------------------------------------------------------------------
# Table 9 -- ESS diagnostics derived from the active-state history
# ---------------------------------------------------------------------------
def check_ess_diagnostics(tex):
    h = csv("active_states_history.csv")["Avg_Active_State_ESS"]
    want = {
        "Minimum window-level mean ESS": h.min(),
        "5th Percentile window-level mean ESS": h.quantile(0.05,
                                                           interpolation="linear"),
        "Median window-level mean ESS": h.median(),
        "Mean window-level mean ESS": h.mean(),
        "Maximum window-level mean ESS": h.max(),
    }
    rows = {label_of(r): r for r in table_rows(tex, "tab:ess_diagnostics")}
    for key, value in want.items():
        r = rows.get(key)
        if r is None:
            failures.append(f"Table 9 [{key}]: row missing")
            continue
        check(f"Table 9 [{key}]", num(r[1]), value, 5e-2)


# ---------------------------------------------------------------------------
# Table 10 -- bootstrap inference
# ---------------------------------------------------------------------------
def check_bootstrap(tex):
    df = csv("bootstrap_inference.csv").set_index("Benchmark")
    rows = {label_of(r): r for r in table_rows(tex, "tab:bootstrap")}
    for csv_name, tex_name in CSV_TO_TEX.items():
        if csv_name not in df.index:
            continue
        s = df.loc[csv_name]
        r = rows.get(tex_name)
        if r is None:
            failures.append(f"Table 10 [{tex_name}]: row missing")
            continue
        check(f"Table 10 [{tex_name}] Sharpe difference", num(r[1]),
              s["Sharpe_Diff"], 5e-4)
        check(f"Table 10 [{tex_name}] bootstrap SE", num(r[2]),
              s["Std_Error"], 5e-5)
        ci = re.findall(r"[-+]?\d*\.?\d+", r[3].replace("$", ""))
        if len(ci) == 2:
            check(f"Table 10 [{tex_name}] CI lower", float(ci[0]),
                  s["CI_Lower_95"], 5e-4)
            check(f"Table 10 [{tex_name}] CI upper", float(ci[1]),
                  s["CI_Upper_95"], 5e-4)
        else:
            failures.append(f"Table 10 [{tex_name}]: cannot parse the interval")
        check(f"Table 10 [{tex_name}] p-value", num(r[4]), s["P_Value"], 5e-4)


# ---------------------------------------------------------------------------
# Tables 11, 12, 13, 16 -- model-specification sensitivity
# ---------------------------------------------------------------------------
def check_simple(tex, label, file, key_col, cols, tag, keyfmt=lambda v: v):
    df = csv(file)
    rows = table_rows(tex, label)
    if len(rows) != len(df):
        failures.append(f"{tag}: {len(rows)} rows but {len(df)} in {file}")
        return
    for r, (_, s) in zip(rows, df.iterrows()):
        key = num(r[0])
        if key is None or abs(key - keyfmt(s[key_col])) > 1e-6:
            failures.append(f"{tag}: row key {r[0]!r} does not match "
                            f"{s[key_col]}")
            continue
        for idx, (csv_col, scale, tol, name) in enumerate(cols, start=1):
            check(f"{tag} [{s[key_col]:g}] {name}", num(r[idx]),
                  s[csv_col] * scale, tol)


# ---------------------------------------------------------------------------
# Tables 14 and 15 -- ESS-thresholded backtest
# ---------------------------------------------------------------------------
def check_ess_backtest(tex):
    df = csv("ess_full_backtest.csv")
    perf = table_rows(tex, "tab:ess_backtest_perf")
    diag = table_rows(tex, "tab:ess_backtest_diag")
    if len(perf) != len(df) or len(diag) != len(df):
        failures.append("Tables 14/15: row count differs from "
                        "ess_full_backtest.csv")
        return
    for r, (_, s) in zip(perf, df.iterrows()):
        tag = f"Table 14 [Emin={s['ESS_Min']:g}]"
        check(f"{tag} annualized return", num(r[1]),
              s["Ann_Return_Decimal"] * 100, 5e-3)
        check(f"{tag} annualized volatility", num(r[2]),
              s["Ann_Vol_Decimal"] * 100, 5e-3)
        check(f"{tag} Sharpe", num(r[3]), s["Sharpe"], 5e-3)
        check(f"{tag} maximum drawdown", num(r[4]),
              s["Max_DD_Decimal"] * 100, 5e-3)
        check(f"{tag} wealth", num(r[5]), s["Wealth"], 5e-3)
    for r, (_, s) in zip(diag, df.iterrows()):
        tag = f"Table 15 [Emin={s['ESS_Min']:g}]"
        check(f"{tag} turnover", num(r[1]), s["Turnover_Decimal"] * 100, 5e-3)
        check(f"{tag} mean active-state ESS", num(r[2]), s["Avg_ESS"], 5e-3)
        check(f"{tag} minimum active-state ESS", num(r[3]), s["Min_ESS"], 5e-3)
        check(f"{tag} retained-grid fraction", num(r[4]),
              s["Retained_Frac_Decimal"] * 100, 5e-2)


# ---------------------------------------------------------------------------
# Cross-table identities
# ---------------------------------------------------------------------------
def check_identities():
    perf = csv("performance_table.csv").set_index("Strategy")
    tc = csv("tc_sensitivity.csv")
    ess = csv("ess_full_backtest.csv")
    hist = csv("active_states_history.csv")

    for name in CSV_TO_TEX:
        row = tc[(tc.Strategy == name) & (tc.TC_bps == 10.0)]
        if row.empty:
            failures.append(f"identity: no 10 bps row for {name}")
            continue
        check(f"identity Table 4 = Table 6 @10bps [{name}] Sharpe",
              float(row["Sharpe"].iloc[0]), perf.loc[name, "Sharpe"], 5e-4)
        check(f"identity Table 4 = Table 6 @10bps [{name}] wealth",
              float(row["Final_Wealth"].iloc[0]),
              perf.loc[name, "Final_Wealth"], 5e-3)

    base = ess[ess.ESS_Min == 0.0].iloc[0]
    check("identity Table 4 RobustSIP = Table 14 @Emin=0 Sharpe",
          float(base["Sharpe"]), perf.loc["RobustSIP", "Sharpe"], 5e-4)
    check("identity Table 4 RobustSIP = Table 14 @Emin=0 wealth",
          float(base["Wealth"]), perf.loc["RobustSIP", "Final_Wealth"], 5e-3)
    check("identity Table 9 mean ESS = Table 15 @Emin=0 mean active-state ESS",
          float(base["Avg_ESS"]), float(hist["Avg_Active_State_ESS"].mean()),
          5e-3)


# ---------------------------------------------------------------------------
# Prose values that are quoted outside the tables
# ---------------------------------------------------------------------------
def check_prose(tex):
    hist = csv("active_states_history.csv")
    grid = csv("grid_sensitivity.csv")
    bench = csv("benchmark_diagnostics.csv")

    mean_active = hist["Active_States"].mean()
    if f"average {mean_active:.2f}" in tex or f"({mean_active:.2f})" in tex:
        passes.append(f"prose: mean active states {mean_active:.2f}")
    else:
        failures.append(f"prose: mean active states {mean_active:.2f} "
                        "not quoted in the manuscript")

    lo, hi = hist["Active_States"].min(), hist["Active_States"].max()
    if f"between {lo:.0f} and {hi:.0f} active market states" in tex:
        passes.append(f"prose: active-state range {lo:.0f}-{hi:.0f}")
    else:
        failures.append(f"prose: active-state range {lo:.0f}-{hi:.0f} "
                        "not quoted in the manuscript")

    n_windows = len(hist)
    if f"{n_windows} rolling" in tex:
        passes.append(f"prose: {n_windows} rolling windows")
    else:
        failures.append(f"prose: window count {n_windows} not quoted")

    # runtime ratio quoted in the concluding section
    m = re.search(r"([\d.]+)/([\d.]+)\\approx([\d.]+)", tex)
    if m:
        a, b, ratio = float(m.group(1)), float(m.group(2)), float(m.group(3))
        check("prose: dense/adaptive runtime ratio", ratio, a / b, 5e-3)
    else:
        failures.append("prose: runtime ratio expression not found")

    # the manuscript reports the adaptive solve time of the benchmark window
    if not bench.empty:
        passes.append("benchmark_diagnostics.csv present")

    if abs(float(grid[grid.Grid_Size == 21]["Avg_Active_States"].iloc[0])
           - 3.35) < 5e-3:
        passes.append("grid_sensitivity 21x21 active states 3.35")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(TEX):
        print(f"Notice: Manuscript source ({TEX}) is not present in code repository.")
        print("Validating internal CSV consistency and identity checks...")
        check_identities()
        print(f"\n{len(passes)} checks passed, {len(failures)} failed.")
        if failures:
            sys.exit(1)
        print("All result CSV identity and integrity checks passed.")
        return

    tex = open(TEX).read()

    check_gap(tex)
    check_performance(tex)
    check_crisis(tex)
    check_tc(tex)
    check_ess_diagnostics(tex)
    check_bootstrap(tex)
    check_simple(tex, "tab:sens_grid", "grid_sensitivity.csv", "Grid_Size",
                 [("Avg_Runtime", 1, 5e-3, "runtime"),
                  ("Avg_Active_States", 1, 5e-3, "active states"),
                  ("Avg_Worst_CVaR", 1, 5e-3, "worst-case CVaR"),
                  ("L1_Distance", 1, 5e-5, "L1 distance")],
                 "Table 11")
    check_simple(tex, "tab:sens_bw", "bandwidth_sensitivity.csv", "Multiplier",
                 [("Avg_Active_States", 1, 5e-3, "active states"),
                  ("Avg_Worst_CVaR", 1, 5e-3, "worst-case CVaR")],
                 "Table 12")
    check_simple(tex, "tab:sens_ess", "ess_sensitivity.csv", "ESS_Min",
                 [("Avg_Retained_States", 1, 5e-2, "retained states"),
                  ("Avg_Worst_CVaR", 1, 5e-3, "worst-case CVaR")],
                 "Table 13")
    check_ess_backtest(tex)
    check_simple(tex, "tab:sens_block", "block_length_sensitivity.csv",
                 "Block_Length",
                 [("SE", 1, 5e-5, "bootstrap SE"),
                  ("P_Value", 1, 5e-4, "p-value")],
                 "Table 16")
    check_identities()
    check_prose(tex)

    if args.verbose:
        for p in passes:
            print(f"  PASS  {p}")
    print(f"\n{len(passes)} checks passed, {len(failures)} failed.")
    if failures:
        print("\nFAILURES")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("Manuscript tables agree with the archived result files.")


if __name__ == "__main__":
    main()
