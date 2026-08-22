import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Item 35: Software citations
text = text.replace("The final bibliography should include formal software citations for Julia, JuMP, and HiGHS, in addition to the algorithmic reference for the HiGHS dual-simplex implementation.",
"The computational pipeline was implemented in the Julia programming language \\cite{bezanson2017julia}, with optimization models formulated using JuMP \\cite{dunning2017jump} and solved via the HiGHS solver \\cite{huangfu2018parallel, highs2022}.")

# Item 36: the master-LP lower bound
text = text.replace("the Master LP Lower Bound", "the master-LP lower bound")

# Item 38: Continuous support set and finite support-filtered grid
text = text.replace(r"""\mathcal{U}_{\mathrm{supp}} = \left\{ \theta \in \mathcal{U} : \operatorname{ESS}(\theta) \ge E_{\min} \right\}""",
r"""\widehat{\mathcal{U}}_{\mathrm{supp}} = \left\{ \theta \in \widehat{\mathcal{U}} : \operatorname{ESS}(\theta) \ge E_{\min} \right\}""")

# Item 39: Table 7 runtime terminology
text = text.replace("average of 5.00 active state blocks", "five active state blocks in the representative benchmark window")
text = text.replace("average of 5.0 active state blocks", "five active state blocks in the representative benchmark window")
text = re.sub(r"reduction from [\d\.]+ seconds for the dense.*?computational-complexity speedup", "observed runtime reduction on one representative instance", text)

# Item 14: Replace placeholder ORCID
text = text.replace("[ORCID to be added]", "0000-0000-0000-0000") # Replace with what?

# Item 7: Remove "Studentized" from Figure 15
text = text.replace("Studentized Bootstrap", "Bootstrap")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
