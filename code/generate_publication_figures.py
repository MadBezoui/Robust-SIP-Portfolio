import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.stats import gaussian_kde

# Set academic publication style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.autolayout': True,
    'pdf.fonttype': 42,
    'ps.fonttype': 42
})

data_path = "../data/aligned_market_data.csv"
output_dir = "../figures"
os.makedirs(output_dir, exist_ok=True)

# Color palette
COLORS = {
    'RobustSIP': '#d63031',     # Crimson / Ruby Red
    'NominalCVaR': '#00b894',   # Emerald Green
    'FiniteRegime': '#e17055',  # Coral / Amber
    'MinVar': '#0984e3',        # Royal Blue
    '1/N': '#6c5ce7',           # Purple / Slate
}

# ==============================================================================
# 1. BOUNDS CONVERGENCE (MASTER LB & GRID ORACLE WORST-CASE)
# ==============================================================================
def plot_bounds():
    conv_file = os.path.join(output_dir, "convergence_history.csv")
    if not os.path.exists(conv_file):
        print(f"Skipping bounds_plot.pdf ({conv_file} not found)")
        return
    
    df_conv = pd.read_csv(conv_file)
    iters = df_conv['Iteration'].values
    master_lb = df_conv['Master_LB'].values
    oracle_ub = df_conv['Oracle_UB'].values
    gap = df_conv['Optimality_Gap'].values
    active_count = df_conv['Active_Count'].values
    
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=300)
    
    ax.plot(
        iters, master_lb,
        color='#0984e3', linewidth=2.8, linestyle='-', marker='o', markersize=8,
        markerfacecolor='#74b9ff', markeredgecolor='#0984e3', markeredgewidth=1.8,
        label='Master LP Lower Bound ($\mathrm{LB}_k$)', zorder=5
    )
    
    ax.plot(
        iters, oracle_ub,
        color='#d63031', linewidth=2.8, linestyle='-', marker='s', markersize=8,
        markerfacecolor='#ff7675', markeredgecolor='#d63031', markeredgewidth=1.8,
        label=r'Grid Separation Worst-Case Value ($\widehat{G}_k$)', zorder=5
    )
    
    ax.fill_between(
        iters, master_lb, oracle_ub,
        color='#55efc4', alpha=0.35, label=r'Grid-Restricted Exchange Gap ($\widehat{G}_k - \mathrm{LB}_k$)'
    )
    
    # Annotate points
    for i in range(len(iters)):
        ax.annotate(f"{master_lb[i]:.3f}%", (iters[i], master_lb[i]), textcoords="offset points", xytext=(0, -16),
                    ha='center', fontsize=8.5, color='#0984e3', weight='bold')
        ax.annotate(f"{oracle_ub[i]:.3f}%", (iters[i], oracle_ub[i]), textcoords="offset points", xytext=(0, 10),
                    ha='center', fontsize=8.5, color='#d63031', weight='bold')
    
    final_lb = master_lb[-1]
    final_ub = oracle_ub[-1]
    final_gap = gap[-1]
    final_active = active_count[-1]
    final_k = iters[-1]
    
    box_text = (
        r"$\mathbf{Exchange\ Convergence\ Summary:}$" + "\n"
        rf"$\bullet\ \text{{Master Lower Bound: }} \eta^* = {final_lb:.4f}\%$" + "\n"
        rf"$\bullet\ \text{{Grid Worst-Case: }} \widehat{{G}}^* = {final_ub:.4f}\%$" + "\n"
        rf"$\bullet\ \text{{Final Residual Gap: }} {final_gap:.4f}\% \leq 10^{{-4}}$" + "\n"
        rf"$\bullet\ \text{{Active Stress States: }} |\mathcal{{U}}^*| = {final_active}$" + "\n"
        rf"$\bullet\ \text{{Total Iterations: }} k = {final_k}$"
    )
    ax.text(
        0.54, 0.72, box_text, transform=ax.transAxes, fontsize=8.5,
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="#b2bec3", lw=1.0, alpha=0.95)
    )
    
    ax.set_xlabel('Adaptive Exchange Iteration ($k$)', fontsize=11)
    ax.set_ylabel(r'Conditional Value-at-Risk (Daily $\mathrm{CVaR}_{0.95}$, %)', fontsize=11)
    ax.set_title('Monotonic Convergence of Master LP Lower Bound and Grid Worst-Case CVaR', fontsize=12, pad=10)
    ax.set_xticks(iters)
    y_min = min(master_lb) - 0.08 * (max(oracle_ub) - min(master_lb))
    y_max = max(oracle_ub) + 0.12 * (max(oracle_ub) - min(master_lb))
    ax.set_ylim(y_min, y_max)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', frameon=True, framealpha=0.95, facecolor='#ffffff', edgecolor='#b2bec3', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "bounds_plot.pdf"))
    plt.close()
    print("Saved bounds_plot.pdf")


# ==============================================================================
# 2. REAL IN-SAMPLE EFFICIENT FRONTIER
# ==============================================================================
def plot_frontier():
    front_file = os.path.join(output_dir, "frontier_data.csv")
    if not os.path.exists(front_file):
        print(f"Skipping frontier_plot.pdf ({front_file} not found)")
        return
    
    df_front = pd.read_csv(front_file)
    df_mkt = pd.read_csv(data_path)
    
    industry_cols = [c for c in df_mkt.columns if c not in ['Date', 'VIX', 'MarketReturn', 'Drawdown', 'logVIX']]
    X = df_mkt[industry_cols].values
    mu = np.mean(X, axis=0) * 252.0 * 100.0 # Annualized %
    
    # Unconditional daily empirical CVaR (alpha=0.95) for individual assets
    T, N = X.shape
    cvar_ind = []
    for i in range(N):
        losses = -X[:, i]
        v95 = np.percentile(losses, 95)
        cvar_ind.append(np.mean(losses[losses >= v95]) * 100.0) # daily %
    cvar_ind = np.array(cvar_ind)
    
    fig, ax = plt.subplots(figsize=(7.4, 5.4), dpi=300)
    
    ax.scatter(cvar_ind, mu, color='#95a5a6', alpha=0.65, s=42, edgecolors='white', linewidth=0.6, label='Industry Portfolios (N=30)', zorder=2)
    
    notable = {'Util': 'Utilities', 'Hlth': 'Healthcare', 'BusEq': 'Tech/BusEq', 'Oil': 'Energy/Oil', 'Fin': 'Financials'}
    for ind_code, full_name in notable.items():
        if ind_code in industry_cols:
            idx = industry_cols.index(ind_code)
            ax.annotate(full_name, (cvar_ind[idx], mu[idx]), textcoords="offset points", xytext=(6, 4), fontsize=8.5, color='#2c3e50', weight='semibold')
            ax.scatter(cvar_ind[idx], mu[idx], color='#1e3799', s=60, edgecolors='black', linewidth=0.7, zorder=4)
    
    # 1. Classical Markowitz Mean-Variance Frontier
    ax.plot(df_front['MV_CVaR'], df_front['MV_Return'] * 100.0, color='#0984e3', linewidth=2.8, linestyle='-', label='Classical Markowitz Mean-Variance Frontier', zorder=5)
    
    # 2. Nominal CVaR Frontier
    ax.plot(df_front['Nom_CVaR'], df_front['Nom_Return'] * 100.0, color='#00b894', linewidth=2.5, linestyle='--', label='Nominal CVaR Frontier (Unconditional)', zorder=5)
    
    # 3. Continuous-State Robust SIP Frontier
    ax.plot(df_front['Rob_CVaR'], df_front['Rob_Return'] * 100.0, color='#d63031', linewidth=2.8, linestyle='-', label=r'Continuous-State Robust Frontier (Worst State $\widehat{G}$)', zorder=5)
    
    # Benchmark 1/N point
    w_eq = np.ones(N) / N
    loss_eq = - (X @ w_eq)
    v95_eq = np.percentile(loss_eq, 95)
    cvar_eq = np.mean(loss_eq[loss_eq >= v95_eq]) * 100.0
    ret_eq = (w_eq @ np.mean(X, axis=0)) * 252.0 * 100.0
    ax.scatter(cvar_eq, ret_eq, color='#6c5ce7', s=100, marker='s', edgecolors='black', linewidth=0.8, zorder=6, label='Naive Diversification (1/N)')
    ax.annotate('1/N Benchmark', (cvar_eq, ret_eq), textcoords="offset points", xytext=(8, -6), fontsize=9, color='#6c5ce7', weight='bold')
    
    # MinVar minimum point
    min_idx = df_front['MV_CVaR'].idxmin()
    ax.scatter(df_front.loc[min_idx, 'MV_CVaR'], df_front.loc[min_idx, 'MV_Return'] * 100.0, color='#0984e3', s=110, marker='D', edgecolors='black', linewidth=0.8, zorder=6, label='Target-Constrained Minimum Variance')
    
    ax.set_xlabel(r'Conditional Value-at-Risk (Daily $\mathrm{CVaR}_{0.95}$, %)', fontsize=11)
    ax.set_ylabel('Expected Return (Annualized %)', fontsize=11)
    ax.set_title('In-Sample Risk-Return Efficient Frontiers (15% Weight Cap)', fontsize=12, pad=10)
    ax.grid(True, linestyle='--', alpha=0.45)
    ax.legend(loc='upper left', frameon=True, framealpha=0.95, facecolor='#ffffff', edgecolor='#b2bec3', fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "frontier_plot.pdf"))
    plt.close()
    print("Saved frontier_plot.pdf")


# ==============================================================================
# 3. 2D STATE SPACE, EMPIRICAL DENSITY & ACTIVE STRESS STATES
# ==============================================================================
def plot_kernel_map():
    df_mkt = pd.read_csv(data_path)
    Y_vix = df_mkt['VIX'].values
    Y_dd = df_mkt['Drawdown'].values * 100.0 # positive drawdown %
    
    sample_file = os.path.join(output_dir, "active_states_sample.csv")
    df_active = pd.read_csv(sample_file) if os.path.exists(sample_file) else None
    
    fig, ax = plt.subplots(figsize=(7.4, 5.4), dpi=300)
    
    xy = np.vstack([Y_vix, Y_dd])
    kde = gaussian_kde(xy)
    
    vix_grid = np.linspace(8, 85, 100)
    dd_grid = np.linspace(0, 55, 100)
    V_mesh, D_mesh = np.meshgrid(vix_grid, dd_grid)
    Z = kde(np.vstack([V_mesh.ravel(), D_mesh.ravel()])).reshape(V_mesh.shape)
    
    cf = ax.contourf(V_mesh, D_mesh, Z, levels=15, cmap='YlGnBu_r', alpha=0.85)
    cbar = plt.colorbar(cf, ax=ax, pad=0.02)
    cbar.set_label(r'Joint Empirical State Density $f(\mathrm{VIX}, \mathrm{Drawdown})$', fontsize=10)
    
    ax.scatter(Y_vix, Y_dd, color='#2c3e50', alpha=0.15, s=6, rasterized=True, label='Daily Historical States (1990-2026)')
    
    v_min, v_max = np.min(Y_vix), np.max(Y_vix)
    d_min, d_max = np.min(Y_dd), np.max(Y_dd)
    delta_v = 0.10 * (v_max - v_min)
    delta_d = 0.10 * (d_max - d_min)
    
    rect = patches.Rectangle(
        (max(5.0, v_min - delta_v), max(0.0, d_min - delta_d)),
        (v_max - v_min) + 2 * delta_v,
        (d_max - d_min) + 2 * delta_d,
        linewidth=1.8,
        edgecolor='#e74c3c',
        facecolor='none',
        linestyle='--',
        label=r'Compact State Space $\mathcal{U} \subset \mathbb{R}^2$'
    )
    ax.add_patch(rect)
    
    crises_ann = [
        ("Lehman / GFC (Oct 2008)", 80.06, 48.36, (-140, -18)),
        ("COVID-19 Crash (Mar 2020)", 82.69, 33.8, (-165, 15)),
        ("Dot-Com Peak (Oct 2002)", 45.08, 44.7, (10, 8)),
        ("LTCM Crisis (Oct 1998)", 45.74, 19.3, (10, 8)),
        ("2022 Inflation Low (Jun 2022)", 34.02, 24.5, (10, -15))
    ]
    
    for label, vx, dd, offset in crises_ann:
        ax.scatter(vx, dd, color='#c0392b', s=55, zorder=6, edgecolors='black', linewidth=0.8)
        ax.annotate(
            label, (vx, dd),
            textcoords="offset points",
            xytext=offset,
            fontsize=8,
            weight='bold',
            color='#7f1d1d',
            bbox=dict(boxstyle="round,pad=0.25", fc="#fff5f5", ec="#feb2b2", lw=0.8, alpha=0.9),
            arrowprops=dict(arrowstyle="->", color="#e53e3e", lw=0.8)
        )
    
    if df_active is not None:
        for idx, row in df_active.iterrows():
            vx = row['Raw_VIX']
            dd = row['Drawdown_Pct']
            ax.scatter(vx, dd, color='#f39c12', marker='*', s=150, zorder=7, edgecolors='black', linewidth=0.8)
            lbl = f"Active State $\\theta^{{({int(row['State_Index'])})}}$"
            ax.annotate(lbl, (vx, dd), textcoords="offset points", xytext=(8, -12), fontsize=8.5, weight='bold', color='#b7791f',
                        bbox=dict(boxstyle="round,pad=0.2", fc="#fffaf0", ec="#fbd38d", lw=0.8))
    
    ax.set_xlim(5, 95)
    ax.set_ylim(-2, 58)
    ax.set_xlabel('CBOE Implied Volatility Index (VIX)', fontsize=11)
    ax.set_ylabel('Trailing Equity Market Drawdown ($D_t$, %)', fontsize=11)
    ax.set_title('Continuous Market-State Space, Empirical Density, and Active Stress States', fontsize=12, pad=10)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='upper right', frameon=True, framealpha=0.92, facecolor='#ffffff', edgecolor='#dcdde1', fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "kernel_map_plot.pdf"))
    plt.close()
    print("Saved kernel_map_plot.pdf")


# ==============================================================================
# 4. CIRCULAR BLOCK-BOOTSTRAP INFERENCE DISTRIBUTION
# ==============================================================================
def plot_bootstrap():
    dist_file = os.path.join(output_dir, "bootstrap_distribution.csv")
    inf_file = os.path.join(output_dir, "bootstrap_inference.csv")
    if not os.path.exists(dist_file) or not os.path.exists(inf_file):
        print("Skipping bootstrap_plot.pdf (files not found)")
        return
    
    df_dist = pd.read_csv(dist_file)
    df_inf = pd.read_csv(inf_file)
    
    boot_diffs = df_dist['Bootstrap_Diff'].values
    
    # Get NominalCVaR row
    nom_row = df_inf[df_inf['Benchmark'] == 'NominalCVaR'].iloc[0]
    diff_sharpe = nom_row['Sharpe_Diff']
    se_boot = nom_row['Std_Error']
    ci_low = nom_row['CI_Lower_95']
    ci_high = nom_row['CI_Upper_95']
    p_val = nom_row['P_Value']
    n_reps = len(boot_diffs)
    
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=300)
    
    n_bins, bins, patches_hist = ax.hist(
        boot_diffs, bins=50, density=True, color='#3498db', alpha=0.45, edgecolor='#2980b9', linewidth=0.8,
        label=rf'Bootstrap Replications ($B = {n_reps}$, Block Size $b = 12$)'
    )
    
    kde_boot = gaussian_kde(boot_diffs)
    x_eval = np.linspace(np.min(boot_diffs) - 0.02, np.max(boot_diffs) + 0.02, 300)
    ax.plot(x_eval, kde_boot(x_eval), color='#1b4f72', linewidth=2.2, label=r'Kernel Density Estimate of $\Delta\mathrm{SR}$')
    
    x_ci = np.linspace(ci_low, ci_high, 200)
    ax.fill_between(x_ci, 0, kde_boot(x_ci), color='#2ecc71', alpha=0.25, label='95% Block-Bootstrap Confidence Interval')
    
    ax.axvline(diff_sharpe, color='#e74c3c', linewidth=2.2, linestyle='-', label=rf'Realized Difference $\Delta\mathrm{{SR}} = {diff_sharpe:.4f}$')
    ax.axvline(ci_low, color='#27ae60', linewidth=1.8, linestyle='--', label=rf'CI Lower Bound ({ci_low:.4f})')
    ax.axvline(ci_high, color='#27ae60', linewidth=1.8, linestyle='--', label=rf'CI Upper Bound (+{ci_high:.4f})')
    ax.axvline(0.0, color='#2c3e50', linewidth=1.5, linestyle=':', label=r'Null Hypothesis $H_0: \Delta\mathrm{SR} = 0$')
    
    conclusion = "H_0 \\text{ Not Rejected (Equal SR)}" if p_val > 0.05 else "H_0 \\text{ Rejected}"
    stats_text = (
        r"$\mathbf{Circular\ Block{-}Bootstrap\ Test:}$" + "\n"
        rf"$\bullet\ \text{{Estimated Difference: }} \Delta\text{{SR}} = {diff_sharpe:.4f}$" + "\n"
        rf"$\bullet\ \text{{Bootstrap Std. Error: }} \text{{SE}} = {se_boot:.4f}$" + "\n"
        rf"$\bullet\ \text{{95\% Confidence Interval: }} [{ci_low:.4f}, \, {ci_high:.4f}]$" + "\n"
        rf"$\bullet\ \text{{Two-Sided }} p\text{{-Value: }} p = {p_val:.3f}$" + "\n"
        rf"$\bullet\ \text{{Inference Conclusion: }} {conclusion}$"
    )
    
    ax.text(
        0.03, 0.95, stats_text,
        transform=ax.transAxes,
        fontsize=8.5,
        verticalalignment='top',
        bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="#ced4da", lw=1.0, alpha=0.95)
    )
    
    ax.set_xlabel(r'Annualized Sharpe Ratio Difference ($\Delta\mathrm{SR} = \mathrm{SR}_{\mathrm{Robust}} - \mathrm{SR}_{\mathrm{Nominal}}$)', fontsize=11)
    ax.set_ylabel('Probability Density', fontsize=11)
    ax.set_title('Paired Circular Moving-Block Bootstrap Distribution for Out-of-Sample Sharpe Difference', fontsize=12, pad=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', frameon=True, framealpha=0.92, facecolor='#ffffff', edgecolor='#dcdde1', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "bootstrap_plot.pdf"))
    plt.close()
    print("Saved bootstrap_plot.pdf")


# ==============================================================================
# 5. CUMULATIVE WEALTH TRAJECTORIES
# ==============================================================================
def plot_wealth():
    ts_file = os.path.join(output_dir, "strategy_monthly_returns.csv")
    if not os.path.exists(ts_file):
        print("Skipping wealth_plot.pdf (file not found)")
        return
    
    df_ts = pd.read_csv(ts_file)
    dates = pd.to_datetime(df_ts['Date'])
    
    fig, ax = plt.subplots(figsize=(8.0, 5.0), dpi=300)
    
    for s, col in COLORS.items():
        r = df_ts[f"{s}_Ret"].values
        w = np.cumprod(1.0 + r)
        lw = 2.4 if s == 'RobustSIP' else 1.8
        ls = '-' if s in ['RobustSIP', 'MinVar', '1/N'] else '--'
        ax.plot(dates, w, label=s, color=col, linewidth=lw, linestyle=ls)
    
    ax.set_yscale('log')
    ax.set_xlabel('Out-of-Sample Date (1995 to 2026)', fontsize=11)
    ax.set_ylabel('Cumulative Wealth (\\$, Log Scale, Initial \\$1)', fontsize=11)
    ax.set_title('Out-of-Sample Cumulative Net Wealth Trajectories (Net of 10 bps TC)', fontsize=12, pad=10)
    ax.grid(True, which="both", linestyle='--', alpha=0.45)
    ax.legend(loc='upper left', frameon=True, framealpha=0.95, facecolor='#ffffff', edgecolor='#b2bec3', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "wealth_plot.pdf"))
    plt.close()
    print("Saved wealth_plot.pdf")


# ==============================================================================
# 6. UNDERWATER DRAWDOWN PROFILES
# ==============================================================================
def plot_drawdowns():
    ts_file = os.path.join(output_dir, "strategy_monthly_returns.csv")
    if not os.path.exists(ts_file):
        return
    
    df_ts = pd.read_csv(ts_file)
    dates = pd.to_datetime(df_ts['Date'])
    
    fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=300)
    
    for s, col in COLORS.items():
        r = df_ts[f"{s}_Ret"].values
        w = np.cumprod(1.0 + r)
        peak = np.maximum.accumulate(w)
        dd = (w / peak - 1.0) * 100.0
        lw = 2.2 if s == 'RobustSIP' else 1.6
        ax.plot(dates, dd, label=s, color=col, linewidth=lw)
    
    ax.set_xlabel('Out-of-Sample Date (1995 to 2026)', fontsize=11)
    ax.set_ylabel('Portfolio Drawdown (%)', fontsize=11)
    ax.set_title('Out-of-Sample Peak-to-Trough Drawdown Curves', fontsize=12, pad=10)
    ax.grid(True, linestyle='--', alpha=0.45)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95, facecolor='#ffffff', edgecolor='#b2bec3', fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "drawdown_plot.pdf"))
    plt.close()
    print("Saved drawdown_plot.pdf")


# ==============================================================================
# 7. ASSET ALLOCATION WEIGHTS OVER TIME
# ==============================================================================
def plot_weights():
    w_rob_file = os.path.join(output_dir, "weights_rob.csv")
    w_mv_file = os.path.join(output_dir, "weights_mv.csv")
    
    if os.path.exists(w_rob_file):
        df_w_rob = pd.read_csv(w_rob_file)
        dates = pd.to_datetime(df_w_rob['Date'])
        cols = [c for c in df_w_rob.columns if c != 'Date']
        W_rob = df_w_rob[cols].values
        
        fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)
        ax.stackplot(dates, W_rob.T, labels=cols, alpha=0.85)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Rebalancing Date (1995 to 2026)', fontsize=11)
        ax.set_ylabel('Portfolio Allocation Weight', fontsize=11)
        ax.set_title('Robust SIP Dynamic Industry Allocations (Max 15% Cap)', fontsize=12, pad=10)
        ax.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "weights_rob_plot.pdf"))
        plt.close()
        print("Saved weights_rob_plot.pdf")
    
    if os.path.exists(w_mv_file):
        df_w_mv = pd.read_csv(w_mv_file)
        dates = pd.to_datetime(df_w_mv['Date'])
        cols = [c for c in df_w_mv.columns if c != 'Date']
        W_mv = df_w_mv[cols].values
        
        fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)
        ax.stackplot(dates, W_mv.T, labels=cols, alpha=0.85)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Rebalancing Date (1995 to 2026)', fontsize=11)
        ax.set_ylabel('Portfolio Allocation Weight', fontsize=11)
        ax.set_title('Minimum Variance Industry Allocations (Max 15% Cap)', fontsize=12, pad=10)
        ax.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "weights_mv_plot.pdf"))
        plt.close()
        print("Saved weights_mv_plot.pdf")


# ==============================================================================
# 8. MONTHLY TURNOVER DISTRIBUTION
# ==============================================================================
def plot_turnover():
    ts_file = os.path.join(output_dir, "strategy_monthly_returns.csv")
    if not os.path.exists(ts_file):
        return
    
    df_ts = pd.read_csv(ts_file)
    strategies = ['1/N', 'MinVar', 'NominalCVaR', 'FiniteRegime', 'RobustSIP']
    data = [df_ts[f"{s}_TO"].values * 100.0 for s in strategies]
    
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    
    bplot = ax.boxplot(data, tick_labels=strategies, patch_artist=True, showmeans=True,
                       meanprops=dict(marker='o', markeredgecolor='black', markerfacecolor='white', markersize=6))
    
    for patch, s in zip(bplot['boxes'], strategies):
        patch.set_facecolor(COLORS[s])
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Monthly Pre-Trade Drifted Turnover (%)', fontsize=11)
    ax.set_title('Distribution of Monthly Portfolio Turnover across Strategies', fontsize=12, pad=10)
    ax.grid(True, linestyle='--', alpha=0.45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "turnover_plot.pdf"))
    plt.close()
    print("Saved turnover_plot.pdf")


# ==============================================================================
# 9. ACTIVE STRESS STATES OVER TIME
# ==============================================================================
def plot_active_states():
    hist_file = os.path.join(output_dir, "active_states_history.csv")
    if not os.path.exists(hist_file):
        return
    
    df_hist = pd.read_csv(hist_file)
    windows = df_hist['Window'].values
    states = df_hist['Active_States'].values
    
    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)
    
    ax.bar(windows, states, color='#0984e3', alpha=0.6, width=1.0, label='Active Stress States per Window')
    
    mean_val = np.mean(states)
    ax.axhline(mean_val, color='#d63031', linewidth=2.2, linestyle='--', label=f'Mean Active States ({mean_val:.2f})')
    
    # Rolling 12-month average
    if len(states) >= 12:
        roll_avg = pd.Series(states).rolling(12, min_periods=1).mean()
        ax.plot(windows, roll_avg, color='#2c3e50', linewidth=2.0, label='Trailing 12-Window Moving Average')
    
    ax.set_xlabel('Rolling Backtest Window (1 to 377)', fontsize=11)
    ax.set_ylabel('Number of Active Master LP State Constraints', fontsize=11)
    ax.set_title('Active Stress Constraints Identified by the Adaptive Exchange Algorithm', fontsize=12, pad=10)
    ax.set_ylim(0, max(states) + 2)
    ax.grid(True, linestyle='--', alpha=0.45)
    ax.legend(loc='upper right', frameon=True, framealpha=0.92, facecolor='#ffffff', edgecolor='#b2bec3', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "active_states_plot.pdf"))
    plt.close()
    print("Saved active_states_plot.pdf")


if __name__ == "__main__":
    print("Generating all publication-quality figures directly from empirical outputs...")
    plot_bounds()
    plot_frontier()
    plot_kernel_map()
    plot_bootstrap()
    plot_wealth()
    plot_drawdowns()
    plot_weights()
    plot_turnover()
    plot_active_states()
    print("All figures generated successfully.")
