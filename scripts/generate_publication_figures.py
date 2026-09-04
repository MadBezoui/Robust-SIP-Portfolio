"""Publication figures for the Continuous-State Robust CVaR portfolio paper.

Figures are authored at the journal text width (120 mm) so that they are
included at scale 1.0 in the manuscript and all lettering lands in the
8-12 pt range required by the publisher.  No figure carries an internal
title: the descriptive text lives in the LaTeX caption, as the artwork
guidelines require.  Series are separated by colour *and* by line style or
marker so that the panels survive greyscale printing and the common forms
of colour vision deficiency.

Run from ``Code/code``:

    python generate_publication_figures.py            # writes ../results
    python generate_publication_figures.py --submission ../../Soumission

The optional second form additionally copies each PDF to ``FigN.pdf`` in
the submission directory, using the figure numbering of the manuscript.
"""

import argparse
import os
import shutil

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, FixedLocator, NullFormatter
from scipy.stats import gaussian_kde

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
# Journal text block is 338 pt = 4.70 in = 119 mm.  Author at that width and
# include with width=\textwidth so no downscaling shrinks the lettering.
TEXT_W = 4.70

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8,
    'axes.labelsize': 8.5,
    'axes.titlesize': 8.5,
    'axes.titleweight': 'normal',
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7,
    'legend.frameon': True,
    'legend.framealpha': 0.92,
    'legend.edgecolor': '#9e9e9e',
    'legend.fancybox': False,
    'legend.borderpad': 0.4,
    'legend.handlelength': 2.4,
    'legend.columnspacing': 1.0,
    'axes.edgecolor': '#4d4d4d',
    'axes.linewidth': 0.7,
    'axes.grid': True,
    'axes.axisbelow': True,
    'grid.color': '#cfcfcf',
    'grid.linestyle': '-',
    'grid.linewidth': 0.4,
    'grid.alpha': 0.8,
    'xtick.major.width': 0.7,
    'ytick.major.width': 0.7,
    'xtick.major.size': 2.6,
    'ytick.major.size': 2.6,
    'lines.solid_capstyle': 'round',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.02,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(ROOT_DIR, "data", "aligned_market_data.csv")
output_dir = os.path.join(ROOT_DIR, "results")
os.makedirs(output_dir, exist_ok=True)

# Okabe-Ito derived palette: distinguishable under deuteranopia/protanopia
# and separable in greyscale once combined with the line styles below.
STRATEGIES = ['RobustSIP', 'NominalCVaR', 'FiniteRegime', 'MinVar', '1/N']
COLORS = {
    'RobustSIP':    '#d55e00',   # vermillion  (focal strategy)
    'NominalCVaR':  '#0072b2',   # blue
    'FiniteRegime': '#009e73',   # bluish green
    'MinVar':       '#cc79a7',   # reddish purple
    '1/N':          '#5a5a5a',   # dark grey
}
STYLES = {
    'RobustSIP':    '-',
    'NominalCVaR':  (0, (5, 1.6)),
    'FiniteRegime': (0, (4, 1.2, 1, 1.2)),
    'MinVar':       (0, (1.4, 1.4)),
    '1/N':          (0, (7, 1.4, 1, 1.4, 1, 1.4)),
}
WIDTHS = {s: (1.5 if s == 'RobustSIP' else 1.0) for s in STRATEGIES}
LABELS = {
    'RobustSIP': 'Robust SIP',
    'NominalCVaR': 'Nominal CVaR',
    'FiniteRegime': 'Finite-regime CVaR',
    'MinVar': 'TC-MinVar',
    '1/N': '$1/N$',
}

GREY_TEXT = '#333333'


def _finish(ax, despine=True):
    """Common axis polish applied to every panel."""
    if despine:
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    ax.tick_params(length=2.6, width=0.7, colors=GREY_TEXT)
    ax.xaxis.label.set_color(GREY_TEXT)
    ax.yaxis.label.set_color(GREY_TEXT)


def _save(fig, name):
    path = os.path.join(output_dir, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved {name}")


def _returns_frame():
    ts_file = os.path.join(output_dir, "strategy_holding_period_returns.csv")
    if not os.path.exists(ts_file):
        return None, None
    df = pd.read_csv(ts_file)
    return df, pd.to_datetime(df['Date'])


def _window_dates(n):
    """Holding-period end dates keyed by backtest window index."""
    cal_file = os.path.join(output_dir, "backtest_calendar.csv")
    if not os.path.exists(cal_file):
        return None
    cal = pd.read_csv(cal_file)
    if 'Hold_End_Date' not in cal.columns or len(cal) < n:
        return None
    return pd.to_datetime(cal['Hold_End_Date']).iloc[:n].values


def _decade_axis(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))


# ==============================================================================
# 1. Cumulative wealth trajectories                                  -> Fig 4
# ==============================================================================
def plot_wealth():
    df_ts, dates = _returns_frame()
    if df_ts is None:
        print("Skipping wealth_plot.pdf (returns file not found)")
        return

    fig, ax = plt.subplots(figsize=(TEXT_W, 3.05))

    finals = {}
    for s in STRATEGIES:
        r = pd.to_numeric(df_ts[f"{s}_Ret"], errors='coerce').values
        # A window with no benchmark solution contributes no growth; the
        # affected dates are flagged in the caption rather than imputed.
        w = np.cumprod(1.0 + np.nan_to_num(r, nan=0.0))
        ax.plot(dates, w, color=COLORS[s], linewidth=WIDTHS[s],
                linestyle=STYLES[s], label=LABELS[s],
                zorder=5 if s == 'RobustSIP' else 3)
        finals[s] = w[-1]

    ax.set_yscale('log')
    ticks = [1, 2, 5, 10, 20, 30]
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(FixedLocator([3, 4, 6, 7, 8, 9, 15, 25]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"\\${v:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(0.75, 46)

    _decade_axis(ax)
    ax.set_xlim(dates.min(), dates.max())
    ax.set_xlabel('Out-of-sample date')
    ax.set_ylabel('Cumulative net wealth (log scale, \\$1 initial)')
    ax.legend(loc='upper left', ncol=2, fontsize=6.8)
    _finish(ax)
    _save(fig, "wealth_plot.pdf")


# ==============================================================================
# 2. Underwater drawdown profiles                                    -> Fig 5
# ==============================================================================
def plot_drawdowns():
    df_ts, dates = _returns_frame()
    if df_ts is None:
        return

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.85))

    curves = {}
    for s in STRATEGIES:
        r = pd.to_numeric(df_ts[f"{s}_Ret"], errors='coerce').values
        w = np.cumprod(1.0 + np.nan_to_num(r, nan=0.0))
        curves[s] = (w / np.maximum.accumulate(w) - 1.0) * 100.0

    # The focal strategy is filled; the benchmarks stay as thin outlines so
    # that five overlapping series remain readable.
    ax.fill_between(dates, curves['RobustSIP'], 0.0,
                    color=COLORS['RobustSIP'], alpha=0.16, linewidth=0, zorder=2)
    for s in STRATEGIES:
        ax.plot(dates, curves[s], color=COLORS[s],
                linewidth=1.4 if s == 'RobustSIP' else 0.75,
                linestyle=STYLES[s], label=LABELS[s],
                alpha=1.0 if s == 'RobustSIP' else 0.85,
                zorder=5 if s == 'RobustSIP' else 3)

    ax.axhline(0.0, color='#4d4d4d', linewidth=0.6)
    _decade_axis(ax)
    ax.set_xlim(dates.min(), dates.max())
    ax.set_ylim(min(c.min() for c in curves.values()) * 1.10, 3)
    ax.set_xlabel('Out-of-sample date')
    ax.set_ylabel('Peak-to-trough drawdown (%)')
    ax.legend(loc='lower left', ncol=3, fontsize=6.6)
    _finish(ax)
    _save(fig, "drawdown_plot.pdf")


# ==============================================================================
# 3. Allocation weights over time                              -> Figs 6 and 7
# ==============================================================================
def _industry_colors(n):
    base = (list(plt.get_cmap('tab20').colors)
            + list(plt.get_cmap('tab20b').colors)
            + list(plt.get_cmap('tab20c').colors))
    return [base[i % len(base)] for i in range(n)]


def _stack_panel(df_w, fname, gap_note=None):
    dates = pd.to_datetime(df_w['Date'])
    cols = [c for c in df_w.columns if c != 'Date']
    W = df_w[cols].apply(pd.to_numeric, errors='coerce').values
    missing = np.isnan(W).any(axis=1)
    W_plot = np.nan_to_num(W, nan=0.0)

    fig, ax = plt.subplots(figsize=(TEXT_W, 3.35))
    colors = _industry_colors(len(cols))
    ax.stackplot(dates, W_plot.T, colors=colors, linewidth=0.0)

    if missing.any():
        # Windows in which the benchmark optimiser returned no solution are
        # drawn as explicit voids rather than left as unexplained white bands.
        for d in np.asarray(dates)[missing]:
            ax.axvline(d, color='#000000', linewidth=1.1, alpha=0.85, zorder=6)
        ax.annotate(gap_note or 'no solution', xy=(0.985, 1.035),
                    xycoords='axes fraction', ha='right', va='bottom',
                    fontsize=6.3, color=GREY_TEXT)

    ax.set_ylim(0, 1)
    ax.set_xlim(dates.min(), dates.max())
    _decade_axis(ax)
    ax.set_xlabel('Rebalancing date')
    ax.set_ylabel('Portfolio allocation weight')
    ax.grid(False)

    handles = [patches.Patch(facecolor=colors[i], edgecolor='none', label=c)
               for i, c in enumerate(cols)]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.20),
              ncol=6, fontsize=6.4, handlelength=1.0, handleheight=0.9,
              handletextpad=0.4, columnspacing=0.9, labelspacing=0.38,
              borderpad=0.35, frameon=False)
    _finish(ax, despine=False)
    _save(fig, fname)


def plot_weights():
    rob = os.path.join(output_dir, "weights_rob.csv")
    mv = os.path.join(output_dir, "weights_mv.csv")
    if os.path.exists(rob):
        _stack_panel(pd.read_csv(rob), "weights_rob_plot.pdf")
    if os.path.exists(mv):
        df = pd.read_csv(mv)
        n_bad = int(df.drop(columns=['Date']).isna().any(axis=1).sum())
        note = (f"vertical rules: {n_bad} of {len(df)} windows with no "
                f"target-constrained solution")
        _stack_panel(df, "weights_mv_plot.pdf", gap_note=note)


# ==============================================================================
# 4. Holding-period turnover distribution                            -> Fig 8
# ==============================================================================
def plot_turnover():
    df_ts, _ = _returns_frame()
    if df_ts is None:
        return

    order = ['1/N', 'MinVar', 'NominalCVaR', 'FiniteRegime', 'RobustSIP']
    series, counts = [], []
    for s in order:
        v = pd.to_numeric(df_ts[f"{s}_TO"], errors='coerce').values * 100.0
        v = v[np.isfinite(v)]
        series.append(v)
        counts.append(len(v))

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.95))
    bp = ax.boxplot(series, patch_artist=True, widths=0.55, showmeans=True,
                    medianprops=dict(color='#1a1a1a', linewidth=1.1),
                    whiskerprops=dict(color='#4d4d4d', linewidth=0.7),
                    capprops=dict(color='#4d4d4d', linewidth=0.7),
                    flierprops=dict(marker='o', markersize=1.8,
                                    markerfacecolor='none',
                                    markeredgecolor='#7a7a7a',
                                    markeredgewidth=0.45),
                    meanprops=dict(marker='D', markersize=3.2,
                                   markerfacecolor='white',
                                   markeredgecolor='#1a1a1a',
                                   markeredgewidth=0.8))
    for patch, s in zip(bp['boxes'], order):
        patch.set_facecolor(COLORS[s])
        patch.set_alpha(0.55)
        patch.set_edgecolor('#4d4d4d')
        patch.set_linewidth(0.7)

    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(['$1/N$', 'TC-MinVar', 'Nominal\nCVaR',
                        'Finite-regime\nCVaR', 'Robust SIP'])

    top = ax.get_ylim()[1]
    for i, (s, v, n) in enumerate(zip(order, series, counts), start=1):
        note = f"med {np.median(v):.1f}%"
        if n != len(df_ts):
            note += f", $n={n}$"
        ax.annotate(note, xy=(i, -0.20), xycoords=('data', 'axes fraction'),
                    ha='center', va='top', fontsize=6.2, color=GREY_TEXT)

    ax.set_ylim(-2, top)
    ax.set_ylabel('Holding-period pre-trade drifted turnover (%)')
    ax.legend(handles=[
        Line2D([], [], color='#1a1a1a', linewidth=1.1, label='median'),
        Line2D([], [], marker='D', linestyle='none', markersize=3.2,
               markerfacecolor='white', markeredgecolor='#1a1a1a',
               label='mean'),
        Line2D([], [], marker='o', linestyle='none', markersize=1.8,
               markerfacecolor='none', markeredgecolor='#7a7a7a',
               label='window beyond 1.5 IQR')],
        loc='upper left', fontsize=6.6)
    ax.grid(axis='x', visible=False)
    _finish(ax)
    _save(fig, "turnover_plot.pdf")


# ==============================================================================
# 5. Cumulative transaction-cost drag                                -> Fig 9
# ==============================================================================
def plot_cumulative_tc_drag():
    df_ts, dates = _returns_frame()
    if df_ts is None:
        return

    tc_rate = 0.0010  # 10 bps
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.85))

    for s in STRATEGIES:
        to = pd.to_numeric(df_ts[f"{s}_TO"], errors='coerce').values
        # Windows without a solution contribute no measured cost; using
        # nancumsum keeps the series continuous instead of truncating it.
        cum = np.nancumsum(to * tc_rate * 100.0)
        ax.plot(dates, cum, color=COLORS[s], linewidth=WIDTHS[s],
                linestyle=STYLES[s], label=LABELS[s],
                zorder=5 if s == 'RobustSIP' else 3)
        ax.annotate(f"{cum[-1]:.1f}", xy=(dates.iloc[-1], cum[-1]),
                    xytext=(3, 0), textcoords='offset points',
                    fontsize=6.2, va='center', color=COLORS[s])

    _decade_axis(ax)
    ax.set_xlim(dates.min(), dates.max())
    ax.margins(x=0.06)
    ax.set_xlabel('Out-of-sample date')
    ax.set_ylabel('Cumulative transaction-cost drag (%)')
    ax.legend(loc='upper left', ncol=2, fontsize=6.8)
    _finish(ax)
    _save(fig, "cumulative_tc_plot.pdf")


# ==============================================================================
# 6. Active state blocks over time                                  -> Fig 10
# ==============================================================================
def plot_active_states():
    hist_file = os.path.join(output_dir, "active_states_history.csv")
    if not os.path.exists(hist_file):
        return
    df = pd.read_csv(hist_file)
    states = df['Active_States'].values
    x = _window_dates(len(states))
    use_dates = x is not None
    if not use_dates:
        x = df['Window'].values

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.55))
    ax.bar(x, states, color='#7fb3d5', edgecolor='none', alpha=0.9,
           width=30 if use_dates else 1.0,
           label='active stress states per window')

    roll = pd.Series(states).rolling(12, min_periods=1).mean()
    ax.plot(x, roll, color='#1a1a1a', linewidth=1.1,
            label='trailing 12-window mean')
    mean_val = float(np.mean(states))
    ax.axhline(mean_val, color=COLORS['RobustSIP'], linewidth=1.1,
               linestyle=(0, (4, 1.6)), label=f'sample mean ({mean_val:.2f})')

    if use_dates:
        _decade_axis(ax)
        ax.set_xlabel('Out-of-sample date')
    else:
        ax.set_xlabel(f'Rolling backtest window (1 to {len(states)})')
    ax.set_ylim(0, states.max() + 2)
    ax.set_ylabel('Active state blocks in the master LP')
    ax.annotate(f'{len(states)} windows, 441 candidate states',
                xy=(0.985, 0.94), xycoords='axes fraction', ha='right',
                va='top', fontsize=6.3, color=GREY_TEXT)
    ax.legend(loc='upper left', fontsize=6.6)
    _finish(ax)
    _save(fig, "active_states_plot.pdf")


# ==============================================================================
# 7. Exchange-algorithm bound convergence                           -> Fig 11
# ==============================================================================
def plot_bounds():
    conv_file = os.path.join(output_dir, "convergence_history.csv")
    if not os.path.exists(conv_file):
        print(f"Skipping bounds_plot.pdf ({conv_file} not found)")
        return
    df = pd.read_csv(conv_file)
    it = df['Iteration'].values
    lb = df['Master_LB'].values
    ub = df['Oracle_UB'].values

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.75))

    ax.fill_between(it, lb, ub, color='#bdbdbd', alpha=0.40, linewidth=0,
                    label=r'grid-restricted gap $\widehat{G}_k-\mathrm{LB}_k$')
    ax.plot(it, lb, color=COLORS['NominalCVaR'], linewidth=1.4, marker='o',
            markersize=4.2, markerfacecolor='white', markeredgewidth=1.1,
            label=r'master LP lower bound $\mathrm{LB}_k$')
    ax.plot(it, ub, color=COLORS['RobustSIP'], linewidth=1.4, marker='s',
            markersize=4.2, markerfacecolor='white', markeredgewidth=1.1,
            linestyle=(0, (5, 1.6)),
            label=r'grid separation worst case $\widehat{G}_k$')

    for k, (a, b) in enumerate(zip(lb, ub)):
        ax.annotate(f"{a:.3f}", (it[k], a), textcoords='offset points',
                    xytext=(0, -11), ha='center', fontsize=6.3,
                    color=COLORS['NominalCVaR'])
        ax.annotate(f"{b:.3f}", (it[k], b), textcoords='offset points',
                    xytext=(0, 7), ha='center', fontsize=6.3,
                    color=COLORS['RobustSIP'])

    ax.set_xticks(it)
    ax.set_xlabel('Master LP solves ($k$)')
    ax.set_ylabel(r'Daily $\mathrm{CVaR}_{0.95}$ (%)')
    span = ub.max() - lb.min()
    ax.set_ylim(lb.min() - 0.18 * span, ub.max() + 0.22 * span)
    ax.legend(loc='lower right', fontsize=6.8)
    _finish(ax)
    _save(fig, "bounds_plot.pdf")


# ==============================================================================
# 8. Effective sample size of the active states                     -> Fig 12
# ==============================================================================
def plot_ess_over_time():
    hist_file = os.path.join(output_dir, "active_states_history.csv")
    if not os.path.exists(hist_file):
        return
    df = pd.read_csv(hist_file)
    ess = df['Avg_Active_State_ESS'].values
    x = _window_dates(len(ess))
    use_dates = x is not None
    if not use_dates:
        x = df['Window'].values

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.55))
    ax.plot(x, ess, color='#6a51a3', linewidth=0.9,
            label='window mean ESS over active states')
    mean_val = float(np.mean(ess))
    ax.axhline(mean_val, color='#1a1a1a', linewidth=0.9,
               linestyle=(0, (4, 1.6)), label=f'sample mean ({mean_val:.1f})')

    i_min = int(np.argmin(ess))
    ax.scatter([x[i_min]], [ess[i_min]], s=22, facecolor='white',
               edgecolor=COLORS['RobustSIP'], linewidth=1.1, zorder=6)
    ax.annotate(f"minimum {ess[i_min]:.2f}", (x[i_min], ess[i_min]),
                textcoords='offset points', xytext=(6, 8), fontsize=6.4,
                color=COLORS['RobustSIP'])

    if use_dates:
        _decade_axis(ax)
        ax.set_xlabel('Out-of-sample date')
    else:
        ax.set_xlabel(f'Rolling backtest window (1 to {len(ess)})')
    ax.set_ylabel('Effective sample size (ESS)')
    ax.set_ylim(-12, ess.max() * 1.12)
    ax.legend(loc='upper left', fontsize=6.6)
    _finish(ax)
    _save(fig, "ess_history_plot.pdf")


# ==============================================================================
# 9. In-sample efficient frontiers                                  -> Fig 13
# ==============================================================================
def plot_frontier():
    front_file = os.path.join(output_dir, "frontier_data.csv")
    if not os.path.exists(front_file):
        print(f"Skipping frontier_plot.pdf ({front_file} not found)")
        return
    df_front = pd.read_csv(front_file)
    df_mkt = pd.read_csv(data_path)

    industry_cols = [c for c in df_mkt.columns
                     if c not in ['Date', 'VIX', 'MarketReturn', 'Drawdown', 'logVIX']]
    X = df_mkt[industry_cols].values
    mu = np.mean(X, axis=0) * 252.0 * 100.0

    cvar_ind = np.array([
        np.mean((-X[:, i])[(-X[:, i]) >= np.percentile(-X[:, i], 95)]) * 100.0
        for i in range(X.shape[1])])

    fig, ax = plt.subplots(figsize=(TEXT_W, 3.15))
    ax.scatter(cvar_ind, mu, s=13, color='#b0b0b0', edgecolors='white',
               linewidth=0.4, zorder=2,
               label=f'industry portfolios ($N={X.shape[1]}$)')

    notable = {'Util': 'Utilities', 'Hlth': 'Health', 'BusEq': 'BusEq',
               'Oil': 'Oil', 'Fin': 'Finance'}
    offsets = {'Util': (5, -8), 'Hlth': (6, 4), 'BusEq': (6, 2),
               'Oil': (5, -8), 'Fin': (5, 3)}
    for code, name in notable.items():
        if code in industry_cols:
            i = industry_cols.index(code)
            ax.scatter(cvar_ind[i], mu[i], s=20, color='#404040', zorder=4)
            ha = 'right' if offsets[code][0] < 0 else 'left'
            ax.annotate(name, (cvar_ind[i], mu[i]), textcoords='offset points',
                        xytext=offsets[code], fontsize=6.4, ha=ha,
                        color=GREY_TEXT)

    ax.plot(df_front['MV_CVaR'], df_front['MV_Return'] * 100.0,
            color=COLORS['MinVar'], linewidth=1.3, linestyle=STYLES['MinVar'],
            zorder=5, label='Markowitz mean-variance frontier')
    ax.plot(df_front['Nom_CVaR'], df_front['Nom_Return'] * 100.0,
            color=COLORS['NominalCVaR'], linewidth=1.3,
            linestyle=STYLES['NominalCVaR'], zorder=5,
            label='nominal (unconditional) CVaR frontier')
    ax.plot(df_front['Rob_CVaR'], df_front['Rob_Return'] * 100.0,
            color=COLORS['RobustSIP'], linewidth=1.6, zorder=6,
            label='grid-restricted robust frontier (worst grid state)')

    w_eq = np.ones(X.shape[1]) / X.shape[1]
    loss_eq = -(X @ w_eq)
    cvar_eq = np.mean(loss_eq[loss_eq >= np.percentile(loss_eq, 95)]) * 100.0
    ret_eq = (w_eq @ np.mean(X, axis=0)) * 252.0 * 100.0
    ax.scatter(cvar_eq, ret_eq, s=34, marker='s', color=COLORS['1/N'],
               edgecolors='white', linewidth=0.6, zorder=7,
               label='naive diversification ($1/N$)')
    ax.annotate('$1/N$', (cvar_eq, ret_eq), textcoords='offset points',
                xytext=(6, -7), fontsize=6.6, color=COLORS['1/N'])

    i_mv = df_front['MV_CVaR'].idxmin()
    ax.scatter(df_front.loc[i_mv, 'MV_CVaR'],
               df_front.loc[i_mv, 'MV_Return'] * 100.0, s=34, marker='D',
               color=COLORS['MinVar'], edgecolors='white', linewidth=0.6,
               zorder=7, label='target-constrained minimum variance')

    ax.set_xlabel(r'Conditional value-at-risk (daily $\mathrm{CVaR}_{0.95}$, %)')
    ax.set_ylabel('Expected return (annualized, %)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.20), ncol=2,
              fontsize=6.3, frameon=False, handlelength=2.0,
              columnspacing=1.2)
    _finish(ax)
    _save(fig, "frontier_plot.pdf")


# ==============================================================================
# 10. Market-state space, density and active states                 -> Fig 14
# ==============================================================================
def plot_kernel_map():
    df_mkt = pd.read_csv(data_path, parse_dates=['Date'])
    # The model indexes states by (log VIX, drawdown); the density is
    # estimated in exactly those coordinates and the axis is relabelled in
    # VIX levels for interpretability.
    lv = df_mkt['logVIX'].values
    dd = df_mkt['Drawdown'].values

    fig, ax = plt.subplots(figsize=(TEXT_W, 3.25))

    kde = gaussian_kde(np.vstack([lv, dd]))
    lv_grid = np.linspace(lv.min() - 0.15, lv.max() + 0.15, 160)
    dd_grid = np.linspace(-0.02, dd.max() + 0.06, 160)
    LV, DD = np.meshgrid(lv_grid, dd_grid)
    Z = kde(np.vstack([LV.ravel(), DD.ravel()])).reshape(LV.shape)

    cf = ax.contourf(LV, DD * 100.0, Z, levels=12, cmap='Blues')
    cbar = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.045)
    cbar.set_label(r'Joint density $f(\log \mathrm{VIX},\, D)$', fontsize=7)
    cbar.ax.tick_params(labelsize=6.4, length=2)

    ax.scatter(lv, dd * 100.0, s=1.6, color='#37474f', alpha=0.20,
               linewidth=0, rasterized=True)

    delta_v = 0.10 * (lv.max() - lv.min())
    delta_d = 0.10 * (dd.max() - dd.min())
    rect = patches.Rectangle(
        (lv.min() - delta_v, max(0.0, dd.min() - delta_d) * 100.0),
        (lv.max() - lv.min()) + 2 * delta_v,
        (min(1.0, dd.max() + delta_d) - max(0.0, dd.min() - delta_d)) * 100.0,
        linewidth=1.1, edgecolor=COLORS['RobustSIP'], facecolor='none',
        linestyle=(0, (4, 1.6)), zorder=6,
        label=r'compact state space $\mathcal{U}\subset\mathbb{R}^2$')
    ax.add_patch(rect)

    # Each marker is a single observed state: the day on which the trailing
    # drawdown troughed within the episode.  Marking one real observation
    # keeps the annotated coordinates consistent with the manuscript text.
    crises = [("LTCM, Oct 1998", "1998-08-01", "1998-12-31", (8, -11)),
              ("Dot-com trough, Jul 2002", "2000-03-01", "2002-12-31", (-7, 7)),
              ("Lehman, Nov 2008", "2008-09-01", "2009-03-31", (-7, 7)),
              ("COVID-19, Mar 2020", "2020-02-01", "2020-04-30", (-7, -11)),
              ("Inflation sell-off, Jun 2022", "2022-01-01", "2022-12-31", (-6, -12))]
    for label, start, end, off in crises:
        sub = df_mkt[(df_mkt['Date'] >= start) & (df_mkt['Date'] <= end)]
        if sub.empty:
            continue
        i = sub['Drawdown'].idxmax()
        x, y = df_mkt['logVIX'][i], df_mkt['Drawdown'][i] * 100.0
        ax.scatter(x, y, s=16, color='#1a1a1a', zorder=8)
        ax.annotate(label, (x, y), textcoords='offset points', xytext=off,
                    fontsize=6.0, color='#1a1a1a',
                    ha='right' if off[0] < 0 else 'left',
                    bbox=dict(boxstyle='round,pad=0.18', fc='white',
                              ec='#9e9e9e', lw=0.4, alpha=0.88), zorder=9)

    sample_file = os.path.join(output_dir, "active_states_sample.csv")
    if os.path.exists(sample_file):
        df_active = pd.read_csv(sample_file)
        ax.scatter(df_active['logVIX'], df_active['Drawdown'] * 100.0,
                   marker='*', s=90, color='#f0c000', edgecolors='#1a1a1a',
                   linewidth=0.6, zorder=10,
                   label=r'active states $\theta^{(j)}$ (representative window)')
        for _, row in df_active.iterrows():
            # Low-drawdown states sit where the legend is, so label upwards.
            off = (7, 3) if row['Drawdown'] > 0.10 else (-8, 7)
            ax.annotate(f"$\\theta^{{({int(row['State_Index'])})}}$",
                        (row['logVIX'], row['Drawdown'] * 100.0),
                        textcoords='offset points', xytext=off,
                        ha='right' if off[0] < 0 else 'left',
                        fontsize=6.4, color='#8a6d00', zorder=11)

    vix_ticks = [10, 15, 20, 30, 45, 65, 85]
    ax.set_xticks(np.log(vix_ticks))
    ax.set_xticklabels([str(v) for v in vix_ticks])
    ax.set_xlim(lv.min() - 0.16, lv.max() + 0.16)
    ax.set_ylim(-2, dd.max() * 100.0 + 8)
    ax.set_xlabel('CBOE volatility index (VIX level, log spacing)')
    ax.set_ylabel('Trailing equity market drawdown $D_t$ (%)')
    handles, labels = ax.get_legend_handles_labels()
    handles.insert(0, Line2D([], [], marker='o', linestyle='none',
                             markersize=2.6, color='#37474f', alpha=0.55))
    labels.insert(0, 'daily historical states (1990-2026)')
    ax.legend(handles, labels, loc='lower right', fontsize=6.2)
    ax.grid(color='white', linewidth=0.35, alpha=0.5)
    _finish(ax, despine=False)
    _save(fig, "kernel_map_plot.pdf")


# ==============================================================================
# 11. Block-bootstrap inference                                     -> Fig 15
# ==============================================================================
def plot_bootstrap():
    dist_file = os.path.join(output_dir, "bootstrap_distribution.csv")
    inf_file = os.path.join(output_dir, "bootstrap_inference.csv")
    if not (os.path.exists(dist_file) and os.path.exists(inf_file)):
        print("Skipping bootstrap_plot.pdf (files not found)")
        return

    diffs = pd.read_csv(dist_file)['Bootstrap_Diff'].values
    row = pd.read_csv(inf_file).query("Benchmark == 'NominalCVaR'").iloc[0]
    d_sr, se = row['Sharpe_Diff'], row['Std_Error']
    ci_lo, ci_hi, p_val = row['CI_Lower_95'], row['CI_Upper_95'], row['P_Value']

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.85))

    ax.hist(diffs, bins=48, density=True, color='#c6dbef',
            edgecolor='#6baed6', linewidth=0.35,
            label=rf'replications ($B={len(diffs)}$, $b=12$)')

    kde = gaussian_kde(diffs)
    xs = np.linspace(diffs.min() - 0.02, diffs.max() + 0.02, 400)
    ax.plot(xs, kde(xs), color='#08519c', linewidth=1.2,
            label=r'kernel density')

    x_ci = np.linspace(ci_lo, ci_hi, 250)
    ax.fill_between(x_ci, 0, kde(x_ci), color='#08519c', alpha=0.14,
                    linewidth=0, label=r'95% interval')

    ax.axvline(d_sr, color=COLORS['RobustSIP'], linewidth=1.3,
               label=rf'realized ${d_sr:.4f}$')
    for b in (ci_lo, ci_hi):
        ax.axvline(b, color='#08519c', linewidth=0.9, linestyle=(0, (4, 1.6)))
    ax.axvline(0.0, color='#1a1a1a', linewidth=0.9, linestyle=(0, (1.4, 1.4)),
               label=r'$H_0:\Delta\mathrm{SR}=0$')

    ax.annotate(rf"$\mathrm{{SE}}={se:.4f}$,  "
                rf"$95\%\,\mathrm{{CI}}=[{ci_lo:.4f},\,{ci_hi:.4f}]$,  "
                rf"$p={p_val:.3f}$",
                xy=(0.5, 1.035), xycoords='axes fraction', ha='center',
                va='bottom', fontsize=6.6, color=GREY_TEXT)

    ax.set_xlabel(r'Annualized Sharpe-ratio difference '
                  r'$\Delta\mathrm{SR}=\mathrm{SR}_{\mathrm{Robust}}'
                  r'-\mathrm{SR}_{\mathrm{Nominal}}$')
    ax.set_ylabel('Probability density')
    ax.set_ylim(0, float(kde(xs).max()) * 1.42)
    ax.legend(loc='upper right', fontsize=6.3, handlelength=1.8)
    _finish(ax)
    _save(fig, "bootstrap_plot.pdf")


# ==============================================================================
# Supplementary: market-state trajectory (not included in the manuscript)
# ==============================================================================
def plot_market_trajectory():
    df_mkt = pd.read_csv(data_path, parse_dates=['Date'])
    dates = df_mkt['Date']

    fig, ax1 = plt.subplots(figsize=(TEXT_W, 2.75))
    ax1.plot(dates, df_mkt['VIX'], color=COLORS['RobustSIP'], linewidth=0.6)
    ax1.set_ylabel('CBOE VIX index', color=COLORS['RobustSIP'])
    ax1.tick_params(axis='y', labelcolor=COLORS['RobustSIP'])
    ax1.set_xlabel('Date')

    ax2 = ax1.twinx()
    ax2.plot(dates, df_mkt['Drawdown'] * 100.0, color=COLORS['NominalCVaR'],
             linewidth=0.6)
    ax2.set_ylabel('Trailing equity market drawdown (%)',
                   color=COLORS['NominalCVaR'])
    ax2.tick_params(axis='y', labelcolor=COLORS['NominalCVaR'])
    ax2.grid(False)

    _decade_axis(ax1)
    ax1.set_xlim(dates.min(), dates.max())
    _finish(ax1, despine=False)
    _save(fig, "market_trajectory_plot.pdf")


# ==============================================================================
# Submission packaging
# ==============================================================================
# Figure numbers 1-3 in the manuscript are TikZ schematics typeset inline, so
# the artwork files start at the fourth figure.
FIGURE_MAP = [
    ("wealth_plot.pdf",        "Fig1.pdf"),
    ("drawdown_plot.pdf",      "Fig2.pdf"),
    ("weights_rob_plot.pdf",   "Fig3.pdf"),
    ("weights_mv_plot.pdf",    "Fig4.pdf"),
    ("turnover_plot.pdf",      "Fig5.pdf"),
    ("cumulative_tc_plot.pdf", "Fig6.pdf"),
    ("active_states_plot.pdf", "Fig7.pdf"),
    ("bounds_plot.pdf",        "Fig8.pdf"),
    ("ess_history_plot.pdf",   "Fig9.pdf"),
    ("frontier_plot.pdf",      "Fig10.pdf"),
    ("kernel_map_plot.pdf",    "Fig11.pdf"),
    ("bootstrap_plot.pdf",     "Fig12.pdf"),
]


def copy_to_submission(dest):
    os.makedirs(dest, exist_ok=True)
    for src_name, dst_name in FIGURE_MAP:
        src = os.path.join(output_dir, src_name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(dest, dst_name))
            print(f"  {src_name} -> {dst_name}")
        else:
            print(f"  MISSING {src_name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", default=None,
                    help="also copy the figures into this directory as FigN.pdf")
    args = ap.parse_args()

    print("Generating publication figures from the empirical outputs...")
    plot_wealth()
    plot_drawdowns()
    plot_weights()
    plot_turnover()
    plot_cumulative_tc_drag()
    plot_active_states()
    plot_bounds()
    plot_ess_over_time()
    plot_frontier()
    plot_kernel_map()
    plot_bootstrap()
    plot_market_trajectory()

    if args.submission:
        print(f"Copying figures into {args.submission}...")
        copy_to_submission(args.submission)
    print("All figures generated successfully.")
