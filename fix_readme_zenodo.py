import re

# Update main_paper.tex
with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()
old_da = r"The code and pre-processed data used to generate the results are available in the official repository \cite{bezoui2026robust}."
new_da = r"All reported results correspond to Zenodo version DOI 10.5281/zenodo.22309074, archived from Git commit 416b0a339040178906642df61a94c25910c11e99. The GitHub repository may contain later development versions \cite{bezoui2026robust}."
text = text.replace(old_da, new_da)
with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)

# Update README.md
with open("README.md", "r") as f:
    readme = f.read()

# Replace all v1.7.0, v1.8.0, v1.8.1 with v1.8.2
readme = re.sub(r"v1\.7\.0-submission-final", "v1.8.2", readme)
readme = re.sub(r"v1\.8\.0", "v1.8.2", readme)
readme = re.sub(r"v1\.8\.1", "v1.8.2", readme)

with open("README.md", "w") as f:
    f.write(readme)

