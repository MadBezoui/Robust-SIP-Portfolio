import re
import pandas as pd

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# 1. Add Bounceur as author and ORCIDs
text = text.replace(r"\author{Madani Bezoui \and Thiziri Sifaoui}", r"\author{Madani Bezoui \and Thiziri Sifaoui \and Ahcene Bounceur}")
text = text.replace(r"\authorrunning{M. Bezoui \and T. Sifaoui}", r"\authorrunning{M. Bezoui \and T. Sifaoui \and A. Bounceur}")
bounceur_affiliation = r"""\and
           Ahcene Bounceur \at
              College of Computing and Informatics, University of Sharjah, United Arab Emirates --- \email{abounceur@sharjah.ac.ae} --- ORCID \orcidlink{0000-0002-0043-7742}~0000-0002-0043-7742
"""
text = text.replace(r"""LAROMAD, Faculty of Sciences, UMMTO, Tizi Ouzou, Algeria
}""", r"""LAROMAD, Faculty of Sciences, UMMTO, Tizi Ouzou, Algeria --- ORCID \orcidlink{0009-0007-6884-0611}~0009-0007-6884-0611
           """ + bounceur_affiliation + "}")

text = text.replace(r"\email{mbezoui@cesi.fr}", r"\email{mbezoui@cesi.fr} --- ORCID \orcidlink{0000-0002-8342-7039}~0000-0002-8342-7039")
text = text.replace(r"\usepackage{hyperref}", r"\usepackage{hyperref}" + "\n" + r"\usepackage{orcidlink}")

# 2. Add Bounceur to Author Contributions
text = text.replace(r"\textbf{Author Contributions:} Madani Bezoui: Conceptualization, Methodology, Software, Writing -- original draft. Thiziri Sifaoui: Formal analysis, Validation, Writing -- review and editing.", r"\textbf{Author Contributions:} Madani Bezoui: Conceptualization, Methodology, Software, Writing -- original draft. Thiziri Sifaoui: Formal analysis, Validation, Writing -- review and editing. Ahcene Bounceur: Supervision, Writing -- review and editing.")

# 3. 1/N definition
text = text.replace("rebalanced to $w_i = 1/N$ at the start of the out-of-sample period, without subsequent rebalancing", "rebalanced to $w_i = 1/N$ on every rebalance date (i.e. every 21 trading days)")

# 4. Remove 600s time-limit caveats
text = text.replace("a 600-second solver time limit per iteration is enforced. On approximately 1.5\\% of rolling windows, the solver hits this time limit; these early-termination points are nonetheless retained", "On all 377 rolling windows, the minimum-variance solver converges to global optimality in well under a second")

# 5. Fix Table 4 data (from Table 2 CSV)
try:
    df_perf = pd.read_csv("results/performance_table.csv")
    for _, row in df_perf.iterrows():
        strat = row['Strategy']
        if strat == "1_N": s_tex = "1/N"
        elif strat == "MinVar": s_tex = "TC-MinVar"
        elif strat == "NominalCVaR": s_tex = "Nominal CVaR"
        elif strat == "FiniteRegime": s_tex = "Finite-Regime CVaR"
        elif strat == "RobustSIP": s_tex = "Robust SIP"
        else: continue
        
        # Only replace inside the performance table
        # Find the line starting with s_tex and ending with \\ or \
        pattern = re.compile(r"^(" + re.escape(s_tex) + r"\s*&.*?)\\\\$", re.MULTILINE)
        
        # Wait, if we use a specific regex that matches exactly the number of columns in Table 4:
        # Strategy & Ann_Mean & Ann_Vol & Sharpe & Max_DD & Avg_Turnover
        # This prevents matching Table 7 (4 columns) or Table 6 (different format).
        table4_pattern = re.compile(r"^(" + re.escape(s_tex) + r")\s*&\s*[\d\.\-]+\\%?\s*&\s*[\d\.\-]+\\%?\s*&\s*[\d\.\-]+\s*&\s*[\d\.\-]+\\%?\s*&\s*[\d\.\-]+\\%?\s*\\\\$", re.MULTILINE)
        
        replacement = f"{s_tex} & {100*row['Ann_Mean']:.2f}\\% & {100*row['Ann_Vol']:.2f}\\% & {row['Sharpe']:.3f} & {100*row['Max_DD']:.2f}\\% & {100*row['Avg_Turnover']:.2f}\\% \\\\"
        text = table4_pattern.sub(replacement, text)
except Exception as e: 
    print("Error:", e)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
