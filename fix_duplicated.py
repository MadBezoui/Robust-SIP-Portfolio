import re
with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Just find "Across block lengths from 6 to 24 holding periods" and replace the rest of the paragraph.
# Let's see what the exact text is.
