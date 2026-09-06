import re

with open("Soumission/references.bib", "r") as f:
    bib = f.read()

old_entry = """@misc{bezoui2026robust,
  author       = {Bezoui, Madani and Sifaoui, Thiziri},
  title        = {{Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation: code, data and numerical outputs}},
  year         = {2026},
  howpublished = {Zenodo},
  note         = {Software archive, release \\texttt{v1.7.0-submission-final}, \\url{https://github.com/MadBezoui/Robust-SIP-Portfolio}},
  doi          = {10.5281/zenodo.22309074},
  url          = {https://doi.org/10.5281/zenodo.22309074}
}"""

new_entry = """@misc{bezoui2026robust,
  author       = {Bezoui, Madani and Sifaoui, Thiziri and Bounceur, Ahc{\\`e}ne},
  title        = {{Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation: code, data and numerical outputs}},
  year         = {2026},
  howpublished = {Zenodo},
  note         = {Software archive, release \\texttt{v1.8.1}, \\url{https://github.com/MadBezoui/Robust-SIP-Portfolio}},
  doi          = {10.5281/zenodo.22309074},
  url          = {https://doi.org/10.5281/zenodo.22309074}
}"""

bib = bib.replace(old_entry, new_entry)

with open("Soumission/references.bib", "w") as f:
    f.write(bib)
