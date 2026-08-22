with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()
import re
text = re.sub(r" Regarding initialization, re-running the 20-window sensitivity subset.*?initial active set\.", "", text)
with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
