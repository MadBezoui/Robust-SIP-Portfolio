with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""Across all block lengths from 6 to 24 holding periods, the bootstrap standard error ranges from approximately 0.0535 to 0.0658
over the considered block lengths, and the corresponding reported
$p$-values remain above 0.18, and the two-sided $p$-value for the Sharpe ratio difference against the Nominal CVaR benchmark never falls below the conventional 0.05 threshold, Across the examined block lengths, all reported $p$-values exceed 0.05. Thus, the qualitative non-rejection conclusion is unchanged, although the estimated standard errors and $p$-values vary with the block length. The block-length sensitivity results use the same methodology as the primary bootstrap analysis. Remaining numerical differences across block lengths reflect both the altered dependence structure induced by the block length and Monte Carlo variability."""

new_text = r"""Across block lengths from 6 to 24 holding periods, the bootstrap
standard error ranges from 0.0535 to 0.0658 and the corresponding
two-sided $p$-values range from 0.183 to 0.281. All reported $p$-values
therefore exceed both the 5\% and 10\% significance thresholds. The
qualitative non-rejection conclusion is unchanged, although the estimated
standard errors and $p$-values vary with block length."""

text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
