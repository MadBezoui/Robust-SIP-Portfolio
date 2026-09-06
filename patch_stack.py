import re

with open("scripts/generate_publication_figures.py", "r") as f:
    text = f.read()

old_func = r"""def _stack_panel(df_w, fname, gap_note=None):
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
    _save(fig, fname)"""

new_func = r"""def _stack_panel(df_w, fname, gap_note=None):
    dates = pd.to_datetime(df_w['Date'])
    cols = [c for c in df_w.columns if c != 'Date']
    W = df_w[cols].apply(pd.to_numeric, errors='coerce').values
    missing = np.isnan(W).any(axis=1)
    W_plot = np.nan_to_num(W, nan=0.0)
    
    # Calculate Effective Number of Assets (ENA)
    ena = np.zeros(len(W_plot))
    for i in range(len(W_plot)):
        sq_sum = np.sum(W_plot[i]**2)
        if sq_sum > 0:
            ena[i] = 1.0 / sq_sum

    fig, ax = plt.subplots(figsize=(TEXT_W, 2.75))
    ax.plot(dates, ena, color='#2c3e50', linewidth=1.2, label='Effective Number of Assets (ENA)')

    if missing.any():
        for d in np.asarray(dates)[missing]:
            ax.axvline(d, color='#000000', linewidth=1.1, alpha=0.85, zorder=6)
        ax.annotate(gap_note or 'no solution', xy=(0.985, 1.035),
                    xycoords='axes fraction', ha='right', va='bottom',
                    fontsize=6.3, color=GREY_TEXT)

    ax.set_ylim(1, len(cols))
    ax.set_xlim(dates.min(), dates.max())
    _decade_axis(ax)
    ax.set_xlabel('Rebalancing date')
    ax.set_ylabel('Effective Number of Assets')
    ax.grid(True, alpha=0.3, ls=':')
    
    _finish(ax)
    _save(fig, fname)"""

text = text.replace(old_func, new_func)

with open("scripts/generate_publication_figures.py", "w") as f:
    f.write(text)
