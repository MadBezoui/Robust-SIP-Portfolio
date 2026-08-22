with open("submission_CompOptAlg_v2/references.bib", "r") as f:
    text = f.read()
# Replace the second occurrence of the block.
# Actually I'll just remove all politis occurrences and append it once.
import re
text = re.sub(r"@article\{politis1992circular[\s\S]*?\}", "", text)
text += "\n@article{politis1992circular,\n  title={A circular block-resampling procedure for stationary data},\n  author={Politis, Dimitris N and Romano, Joseph P},\n  journal={Exploring the limits of bootstrap},\n  pages={263--270},\n  year={1992},\n  publisher={John Wiley \\& Sons}\n}\n"
with open("submission_CompOptAlg_v2/references.bib", "w") as f:
    f.write(text)
