with open("submission_CompOptAlg_v2/references.bib", "a") as f:
    f.write("\n@article{politis1992circular,\n  title={A circular block-resampling procedure for stationary data},\n  author={Politis, Dimitris N and Romano, Joseph P},\n  journal={Exploring the limits of bootstrap},\n  pages={263--270},\n  year={1992},\n  publisher={John Wiley \\& Sons}\n}\n")

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

text = text.replace("paired circular moving-block bootstrap", "paired circular moving-block bootstrap \\cite{politis1992circular}")
# If there are multiple, it's fine.

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
