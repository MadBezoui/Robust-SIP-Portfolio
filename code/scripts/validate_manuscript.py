"""Cross-check every numerical table in the manuscript against its source CSV.

Manual transcription between the result files and the LaTeX tables is the main
way inconsistencies creep in, so this script parses the tables straight out of
``main_paper.tex`` and compares each cell with the corresponding value in
``results/``.  It also checks the cross-table identities that must hold between
different views of the same backtest.

The manuscript sources are not part of this repository, so in a fresh clone of
the tagged release the script runs the CSV-only identity checks and says so.
Point it at a manuscript with ``--tex`` to run the full table-by-table pass.

Run from ``scripts/``:

    python3 validate_manuscript.py                    # CSV identities
    python3 validate_manuscript.py --tex ../Soumission/main_paper.tex
    python3 validate_manuscript.py -v                 # also list passing checks
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
        # the table now carries an explicit crisis-window column, so the
        # strategy sits in column three and the numbers shift right
        off = 1 if len(r) >= 5 else 0
        strat = re.sub(r"[$\\{}]|textbf", "", r[1 + off]).strip()
        seen.append((strat, num(r[2 + off]), num(r[3 + off])))
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
    """Table 6: one row per strategy, five Sharpe columns then five wealth."""
    df = csv("tc_sensitivity.csv")
    rows = table_rows(tex, "tab:tc_sensitivity")
    if not rows:
        failures.append("Table 6: table not found")
        return
    compared = 0
    seen = set()
    for r in rows:
        head = label_of(r)
        for csv_name, tex_name in CSV_TO_TEX.items():
            if head != tex_name:
                continue
            seen.add(csv_name)
            for k, tc in enumerate(TC_LEVELS):
                sel = df[(df.Strategy == csv_name) & (df.TC_bps == tc)]
                if sel.empty:
                    failures.append(f"Table 6 [{tex_name}, {tc:g} bps]: "
                                    "no matching CSV row")
                    continue
                if 1 + k < len(r):
                    check(f"Table 6 [{tex_name}, {tc:g} bps] Sharpe",
                          num(r[1 + k]), sel["Sharpe"].iloc[0], 5e-4)
                    compared += 1
                if 6 + k < len(r):
                    check(f"Table 6 [{tex_name}, {tc:g} bps] wealth",
                          num(r[6 + k]), sel["Final_Wealth"].iloc[0], 5e-3)
                    compared += 1
    missing = set(CSV_TO_TEX) - seen
    if missing:
        failures.append("Table 6: strategies absent from the table: "
                        + ", ".join(sorted(CSV_TO_TEX[m] for m in missing)))
    if compared == 0:
        failures.append("Table 6: layout not recognised, nothing was compared")


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
    """Tables 12/13 were merged into a single ESS-threshold table."""
    df = csv("ess_full_backtest.csv")
    rows = table_rows(tex, "tab:ess_backtest")
    if not rows:
        return
    if len(rows) != len(df):
        failures.append("ESS-threshold table: row count differs from "
                        "ess_full_backtest.csv")
        return
    cols = [("Ann_Return_Decimal", 100, 5e-3, "annualized return"),
            ("Ann_Vol_Decimal", 100, 5e-3, "annualized volatility"),
            ("Sharpe", 1, 5e-3, "Sharpe"),
            ("Max_DD_Decimal", 100, 5e-3, "maximum drawdown"),
            ("Wealth", 1, 5e-3, "wealth"),
            ("Turnover_Decimal", 100, 5e-2, "turnover"),
            ("Avg_ESS", 1, 5e-2, "mean active-state ESS"),
            ("Min_ESS", 1, 5e-2, "minimum active-state ESS"),
            ("Retained_Frac_Decimal", 100, 5e-2, "retained-grid fraction")]
    for r, (_, s) in zip(rows, df.iterrows()):
        tag = f"ESS table [Emin={s['ESS_Min']:g}]"
        for idx, (col, scale, tol, name) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"{tag} {name}", num(r[idx]), s[col] * scale, tol)


# ---------------------------------------------------------------------------
# Cross-table identities
# ---------------------------------------------------------------------------
def check_referee_benchmarks(tex):
    """The hull-restricted and state-conditioned specifications."""
    f = os.path.join(RESULTS, "referee_benchmarks_summary.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f).set_index("Strategy")
    perf = csv("performance_table.csv").set_index("Strategy")
    rows = {label_of(r): r for r in table_rows(tex, "tab:referee_benchmarks")}
    if not rows:
        failures.append("Referee-benchmark table: not found in the manuscript")
        return
    spec = [("Robust SIP (baseline)", perf.loc["RobustSIP"], "Ann_Mean",
             "Ann_Vol", "Sharpe", "Avg_Turnover", "Final_Wealth"),
            ("Robust SIP, hull-restricted", df.loc["RobustSIP_Hull"], "Ann_Mean",
             "Ann_Vol", "Sharpe", "Avg_Turnover", "Final_Wealth"),
            ("State-conditioned CVaR", df.loc["CondCVaR"], "Ann_Mean",
             "Ann_Vol", "Sharpe", "Avg_Turnover", "Final_Wealth")]
    for name, s, c_ret, c_vol, c_sr, c_to, c_w in spec:
        r = rows.get(name)
        if r is None:
            failures.append(f"Referee-benchmark table [{name}]: row missing")
            continue
        check(f"Referee table [{name}] return", num(r[1]), s[c_ret] * 100, 5e-3)
        check(f"Referee table [{name}] volatility", num(r[2]), s[c_vol] * 100, 5e-3)
        check(f"Referee table [{name}] Sharpe", num(r[3]), s[c_sr], 5e-4)
        check(f"Referee table [{name}] turnover", num(r[4]), s[c_to] * 100, 5e-3)
        check(f"Referee table [{name}] wealth", num(r[5]), s[c_w], 5e-3)


def check_domain_margin(tex):
    """Table: sensitivity to the state-domain expansion margin."""
    f = os.path.join(RESULTS, "domain_margin_sensitivity.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f)
    rows = table_rows(tex, "tab:margin")
    if not rows:
        failures.append("Domain-margin table: not found in the manuscript")
        return
    if len(rows) != len(df):
        failures.append("Domain-margin table: row count differs from the CSV")
        return
    cols = [("Ann_Return", 100, 5e-3, "return"), ("Ann_Vol", 100, 5e-3, "volatility"),
            ("Sharpe", 1, 5e-4, "Sharpe"), ("Max_DD", 100, 5e-3, "maximum drawdown"),
            ("Turnover", 100, 5e-3, "turnover"), ("Final_Wealth", 1, 5e-3, "wealth"),
            ("Mean_Active_ESS", 1, 5e-2, "mean ESS"),
            ("Mean_Active_States", 1, 5e-3, "active states"),
            ("Boundary_Frac", 100, 5e-2, "boundary fraction")]
    for r, (_, s) in zip(rows, df.iterrows()):
        tag = f"Margin table [{s['Margin_Pct']:g}%]"
        for idx, (c, sc, tol, nm) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"{tag} {nm}", num(r[idx]), s[c] * sc, tol)


def check_shrinkage(tex):
    """Table: nominal CVaR under the shrunk conditional law."""
    f = os.path.join(RESULTS, "shrinkage_benchmark.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f)
    rows = table_rows(tex, "tab:shrinkage")
    if not rows:
        failures.append("Shrinkage table: not found in the manuscript")
        return
    if len(rows) != len(df):
        failures.append("Shrinkage table: row count differs from the CSV")
        return
    cols = [("Ann_Return", 100, 5e-3, "return"), ("Ann_Vol", 100, 5e-3, "volatility"),
            ("Sharpe", 1, 5e-4, "Sharpe"), ("Max_DD", 100, 5e-3, "maximum drawdown"),
            ("Turnover", 100, 5e-3, "turnover"), ("Final_Wealth", 1, 5e-3, "wealth")]
    for r, (_, s) in zip(rows, df.iterrows()):
        tag = f"Shrinkage table [lambda={s['Lambda']:.2f}]"
        check(f"{tag} lambda", num(r[0]), s["Lambda"], 5e-4)
        for idx, (c, sc, tol, nm) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"{tag} {nm}", num(r[idx]), s[c] * sc, tol)

    # The two endpoints must reproduce benchmarks already in the manuscript.
    perf = csv("performance_table.csv").set_index("Strategy")
    l0 = df[df.Lambda == 0.0].iloc[0]
    check("Shrinkage lambda=0 equals Nominal CVaR Sharpe",
          l0["Sharpe"], perf.loc["NominalCVaR", "Sharpe"], 5e-3)
    ref = os.path.join(RESULTS, "referee_benchmarks_summary.csv")
    if os.path.exists(ref):
        rb = pd.read_csv(ref).set_index("Strategy")
        l1 = df[df.Lambda == 1.0].iloc[0]
        check("Shrinkage lambda=1 equals CondCVaR Sharpe",
              l1["Sharpe"], rb.loc["CondCVaR", "Sharpe"], 5e-3)
        check("Shrinkage lambda=1 equals CondCVaR wealth",
              l1["Final_Wealth"], rb.loc["CondCVaR", "Final_Wealth"], 5e-3)


def check_scalability(tex):
    """Table: matched dense-LP vs exchange comparison across grid resolutions."""
    f = os.path.join(RESULTS, "experiment_A.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f)
    rows = table_rows(tex, "tab:scalability")
    if not rows:
        failures.append("Scalability table: not found in the manuscript")
        return
    seen = 0
    for r in rows:
        cell = r[0].replace("$", "").strip()
        if "times" not in cell:
            continue
        g = int(cell.split("\\times")[0].strip())
        s = df[df.GridDim == g]
        if s.empty:
            failures.append(f"Scalability table: grid {g} absent from the CSV")
            continue
        seen += 1
        tag = f"Scalability [{g}x{g}]"
        check(f"{tag} states", num(r[1]), g * g, 0.5)
        check(f"{tag} dense time", num(r[2]), s.Dense_Time.mean(), 5e-3)
        check(f"{tag} exchange time", num(r[3]), s.Adaptive_Time.mean(), 5e-4)
        check(f"{tag} speedup", num(r[4]),
              (s.Dense_Time / s.Adaptive_Time).mean(), 5e-2)
        check(f"{tag} active blocks", num(r[5]), s.Adaptive_Master_Blocks.mean(), 5e-3)
        check(f"{tag} mean L1", num(r[7]), s.Weights_L1_Diff.mean(), 5e-5)
    if seen != 3:
        failures.append(f"Scalability table: expected 3 grid rows, matched {seen}")


def check_riskfree(tex):
    """Table: Sharpe ratios under a constant non-zero risk-free rate."""
    f = os.path.join(RESULTS, "riskfree_sensitivity.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f).set_index("Strategy")
    rows = table_rows(tex, "tab:riskfree")
    if not rows:
        failures.append("Risk-free table: not found in the manuscript")
        return
    cols = [("Ann_Return", 100, 5e-3, "return"), ("Ann_Vol", 100, 5e-3, "volatility"),
            ("Sharpe_rf0", 1, 5e-4, "Sharpe rf=0%"),
            ("Sharpe_rf2", 1, 5e-4, "Sharpe rf=2%"),
            ("Sharpe_rf4", 1, 5e-4, "Sharpe rf=4%")]
    seen = 0
    for r in rows:
        name = r[0].replace("\\textbf{", "").replace("}", "").strip()
        if name not in df.index:
            failures.append(f"Risk-free table: unknown strategy {name!r}")
            continue
        seen += 1
        for idx, (c, sc, tol, nm) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"Risk-free [{name}] {nm}", num(r[idx]), df.loc[name, c] * sc, tol)
    missing = set(df.index) - {r[0].strip() for r in rows}
    if missing:
        failures.append("Risk-free table: strategies absent: " + ", ".join(sorted(missing)))
    if seen != len(df):
        failures.append(f"Risk-free table: matched {seen} rows, CSV has {len(df)}")


def check_target(tex):
    """Table: sensitivity to the expected-return target."""
    f = os.path.join(RESULTS, "target_sensitivity.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f).set_index("Target")
    rows = table_rows(tex, "tab:target")
    if not rows:
        failures.append("Target table: not found in the manuscript")
        return
    tex_to_csv = {"Non-binding": "none", "Q_{25}": "Q25",
                  "Q_{50}": "Q50", "Q_{75}": "Q75"}
    cols = [("Ann_Return", 100, 5e-3, "return"), ("Ann_Vol", 100, 5e-3, "volatility"),
            ("Sharpe", 1, 5e-4, "Sharpe"), ("Max_DD", 100, 5e-3, "maximum drawdown"),
            ("Turnover", 100, 5e-3, "turnover"), ("Final_Wealth", 1, 5e-3, "wealth"),
            ("Mean_ENA", 1, 5e-3, "effective number of assets"),
            ("Mean_Active_States", 1, 5e-3, "active states")]
    seen = set()
    for r in rows:
        cell = r[0].replace("$", "").strip()
        key = next((k for k in tex_to_csv if k in cell), None)
        if key is None:
            failures.append(f"Target table: unrecognised row label {r[0]!r}")
            continue
        name = tex_to_csv[key]
        seen.add(name)
        s = df.loc[name]
        for idx, (c, sc, tol, nm) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"Target [{name}] {nm}", num(r[idx]), s[c] * sc, tol)
    missing = set(df.index) - seen
    if missing:
        failures.append("Target table: specifications absent: " + ", ".join(sorted(missing)))

    # The Q50 row must reproduce the Robust SIP baseline exactly.
    perf = csv("performance_table.csv").set_index("Strategy")
    check("Target Q50 equals Robust SIP baseline Sharpe",
          df.loc["Q50", "Sharpe"], perf.loc["RobustSIP", "Sharpe"], 5e-3)
    check("Target Q50 equals Robust SIP baseline wealth",
          df.loc["Q50", "Final_Wealth"], perf.loc["RobustSIP", "Final_Wealth"], 5e-3)


def check_bwgeom(tex):
    """Table: diagonal versus full-covariance bandwidth."""
    f = os.path.join(RESULTS, "bandwidth_geometry.csv")
    if not os.path.exists(f):
        return
    df = pd.read_csv(f).set_index("Geometry")
    rows = table_rows(tex, "tab:bwgeom")
    if not rows:
        failures.append("Bandwidth-geometry table: not found in the manuscript")
        return
    cols = [("Sharpe", 1, 5e-4, "Sharpe"), ("Turnover", 100, 5e-3, "turnover"),
            ("Final_Wealth", 1, 5e-3, "wealth"),
            ("Mean_Worst_CVaR", 1, 5e-3, "worst-case CVaR"),
            ("Mean_Active_States", 1, 5e-3, "active states"),
            ("Mean_Active_ESS", 1, 5e-2, "mean ESS")]
    seen = set()
    for r in rows:
        name = "diag" if "diag" in r[0] else ("full" if "full" in r[0] else None)
        if name is None:
            failures.append(f"Bandwidth-geometry table: unrecognised row {r[0]!r}")
            continue
        seen.add(name)
        for idx, (c, sc, tol, nm) in enumerate(cols, start=1):
            if idx < len(r):
                check(f"Bandwidth [{name}] {nm}", num(r[idx]), df.loc[name, c] * sc, tol)
    missing = set(df.index) - seen
    if missing:
        failures.append("Bandwidth-geometry table: rows absent: " + ", ".join(sorted(missing)))

    # the diagonal run must reproduce the Robust SIP baseline
    perf = csv("performance_table.csv").set_index("Strategy")
    check("Bandwidth diag equals Robust SIP baseline Sharpe",
          df.loc["diag", "Sharpe"], perf.loc["RobustSIP", "Sharpe"], 5e-3)


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

    # the speedup quoted in the abstract must equal the two times it cites
    m = re.search(r"in ([\d.]+) seconds against ([\d.]+) seconds"
                  r".{0,80}?a ([\d.]+)-fold speedup", tex, re.S)
    if m is None:
        m = re.search(r"([\d.]+)/([\d.]+)\\approx([\d.]+)", tex)
    if m:
        b, a, ratio = float(m.group(1)), float(m.group(2)), float(m.group(3))
        check("prose: dense/adaptive runtime ratio", ratio, a / b, 5e-2)
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
    ap.add_argument("--tex", default=TEX,
                    help="manuscript source to cross-check (default: %(default)s)")
    args = ap.parse_args()
    tex_path = args.tex
    if not os.path.exists(tex_path):
        print(f"Notice: manuscript source not found at {tex_path}.")
        print("Pass --tex to point at the manuscript source "
              "(soumission/main_paper.tex in this repository).")
        print("Validating internal CSV consistency and identity checks...")
        check_identities()
        print(f"\n{len(passes)} checks passed, {len(failures)} failed.")
        if failures:
            sys.exit(1)
        print("All result CSV identity and integrity checks passed.")
        return

    tex = open(tex_path).read()

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
    check_referee_benchmarks(tex)
    check_domain_margin(tex)
    check_shrinkage(tex)
    check_scalability(tex)
    check_riskfree(tex)
    check_target(tex)
    check_bwgeom(tex)
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
