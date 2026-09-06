import re

with open("scripts/generate_publication_figures.py", "r") as f:
    text = f.read()

# find plot_bounds
start_idx = text.find("def plot_bounds():")
end_idx = text.find("def plot_ess_history():")

if start_idx != -1 and end_idx != -1:
    new_func = r"""def plot_bounds():
    conv_file = os.path.join(output_dir, "convergence_history.csv")
    if not os.path.exists(conv_file):
        print(f"Skipping bounds_plot.pdf ({conv_file} not found)")
        return
    df = pd.read_csv(conv_file)
    it = df['Iteration'].values
    lb = df['Master_LB'].values
    ub = df['Oracle_UB'].values
    gap = ub - lb

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(TEXT_W, 4.0), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    
    # Top panel: Bounds
    ax1.fill_between(it, lb, ub, color='#bdbdbd', alpha=0.40, linewidth=0, label=r'grid-restricted gap $\widehat{G}_k-\mathrm{LB}_k$')
    ax1.plot(it, lb, color=COLORS['NominalCVaR'], linewidth=1.4, marker='o', markersize=4.2, markerfacecolor='white', markeredgewidth=1.1, label=r'master LP lower bound $\mathrm{LB}_k$')
    ax1.plot(it, ub, color=COLORS['RobustSIP'], linewidth=1.4, marker='s', markersize=4.2, markerfacecolor='white', markeredgewidth=1.1, linestyle=(0, (5, 1.6)), label=r'grid separation worst case $\widehat{G}_k$')
    
    ax1.annotate(f"Final gap: {gap[-1]:.1e}", xy=(it[-1], ub[-1]), xytext=(10, 0), textcoords='offset points', va='center', fontsize=7, color='black')

    ax1.set_ylabel("CVaR bound")
    ax1.legend(loc='lower right', frameon=False, fontsize=7.2)
    ax1.grid(True, alpha=0.3, ls=':')
    
    # Bottom panel: Log-scale gap
    ax2.plot(it, gap, color='black', linewidth=1.2, marker='x', markersize=4)
    ax2.axhline(y=1e-4, color='red', linestyle='--', linewidth=1.0, alpha=0.7, label='Tolerance ($10^{-4}$)')
    ax2.set_yscale('log')
    ax2.set_ylabel("Gap (log)")
    ax2.set_xlabel("Adaptive exchange iteration index $k$")
    ax2.set_xticks(range(1, max(it)+1))
    ax2.legend(loc='upper right', frameon=False, fontsize=7.2)
    ax2.grid(True, alpha=0.3, ls=':')
    
    _finish(ax1)
    _finish(ax2)
    _save(fig, "bounds_plot.pdf")

# ==============================================================================
# 8. """
    text = text[:start_idx] + new_func + text[end_idx + 82:] # skipping the comment header

with open("scripts/generate_publication_figures.py", "w") as f:
    f.write(text)
