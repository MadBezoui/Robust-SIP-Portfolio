import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

proofs = re.findall(r"\\begin\{proof\}(.*?)\\end\{proof\}", text, re.DOTALL)

# Replace each proof with a reference
for i, p in enumerate(proofs):
    text = text.replace(r"\begin{proof}" + p + r"\end{proof}", f"\\textit{{Proof is provided in Appendix A.{i+1}.}}\n")

# Append to end before end{document}
appendix_text = "\n\\section*{Appendix: Extended Proofs}\\label{app:proofs}\n"
for i, p in enumerate(proofs):
    appendix_text += f"\n\\subsection*{{A.{i+1} Proof of corresponding theorem/lemma}}\n\\begin{{proof}}{p}\\end{{proof}}\n"

text = text.replace(r"\end{document}", appendix_text + "\n\\end{document}")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
print("Proofs moved to appendix")
