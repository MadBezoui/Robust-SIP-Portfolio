with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

# We will just replace the whole Data Availability section
start_tag = r"\section*{Data availability}"
end_tag = r"\section*{Declarations}"

old_section = re.search(start_tag + r".*?" + end_tag, text, re.DOTALL)
if old_section:
    new_section = r"""\section*{Data availability}
The historical US equity return data and industry portfolio classifications analyzed during the current study are provided by the Center for Research in Security Prices (CRSP) and Kenneth R. French's data library. CBOE Volatility Index (VIX) historical data are available from the Chicago Board Options Exchange. The code, processed data, and archived numerical outputs used to generate the reported results are available in the versioned GitHub release and annotated tag identified by \citet{bezoui2026robust}, subject to the terms of the original data providers.

\section*{Declarations}"""
    text = text.replace(old_section.group(0), new_section)
    with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
        f.write(text)
else:
    print("Could not find Data availability section!")
