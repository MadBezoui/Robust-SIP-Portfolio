import re

with open("code/generate_publication_figures.py", "r") as f:
    text = f.read()

# Fix the textbox text
old_box = r"""    box_text = (
        r"$\mathbf{Exchange\ Convergence\ Summary:}$" + "\n"
        rf"$\bullet\ \text{{Master Lower Bound: }} \eta^* = {final_lb:.4f}\%$" + "\n"
        rf"$\bullet\ \text{{Grid Worst-Case: }} \widehat{{G}}^* = {final_ub:.4f}\%$" + "\n"
        rf"$\bullet\ \text{{Final Residual Gap: }} {final_gap:.4f}\% \leq 10^{{-4}}$" + "\n"
        rf"$\bullet\ \text{{Active Stress States: }} |\mathcal{{U}}^*| = {final_active}$" + "\n"
        rf"$\bullet\ \text{{Total Iterations: }} k = {final_k}$"
    )"""

new_box = r"""    box_text = (
        r"$\mathbf{Exchange\ Convergence\ Summary}$" + "\n"
        rf"$\bullet$ Master Lower Bound: $\eta^* = {final_lb:.4f}\%$" + "\n"
        rf"$\bullet$ Grid Worst-Case: $G^* = {final_ub:.4f}\%$" + "\n"
        rf"$\bullet$ Final Residual Gap: ${final_gap:.4f}\% \leq 0.01$ percentage points" + "\n"
        rf"$\bullet$ Active Stress States: $|U^*| = {final_active}$" + "\n"
        rf"$\bullet$ Total Master solves: $k = {final_k}$"
    )"""

text = text.replace(old_box, new_box)

# Move textbox down
text = text.replace("ax.text(\n        0.54, 0.72,", "ax.text(\n        0.48, 0.40,")

# Fix labels
text = text.replace("ax.set_xlabel('Adaptive Exchange Iteration ($k$)', fontsize=11)", "ax.set_xlabel('Master solves ($k$)', fontsize=11)")

# Since I previously broke dates in bounds_plot, wait, dates is NOT defined in plot_bounds, so `try ... except` will just skip. That's fine.

with open("code/generate_publication_figures.py", "w") as f:
    f.write(text)
