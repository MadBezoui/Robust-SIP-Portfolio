with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""\textbf{Data Availability:} The Kenneth French 30 Industry Portfolio returns \cite{french2026data} and CBOE VIX observations \cite{cboe2026vix} used in this study were obtained from their publicly accessible source pages. Source URLs, retrieval information, preprocessing code, and the aligned research dataset are documented in the accompanying repository, subject to the original providers' terms of use. The code, processed data, and archived numerical outputs used to generate
the reported results are available in the versioned GitHub release and annotated tag identified by Bezoui and Sifaoui [6]
identified by \citet{bezoui2026robust}, subject to the terms of the original
data providers."""

new_text = r"""\textbf{Data Availability:} The Kenneth French 30 Industry Portfolio returns \cite{french2026data} and CBOE VIX observations \cite{cboe2026vix} used in this study were obtained from their publicly accessible source pages. Source URLs, retrieval information, preprocessing code, and the aligned research dataset are documented in the accompanying repository, subject to the original providers' terms of use. The code, processed data, and archived numerical outputs used to generate the reported results are available in the versioned GitHub release and annotated tag identified by \citet{bezoui2026robust}, subject to the terms of the original data providers."""

text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
