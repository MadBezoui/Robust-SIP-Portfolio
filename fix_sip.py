with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

text = text.replace("convex Semi-Infinite Program (SIP)", "convex semi-infinite program (SIP)")
text = text.replace("Semi-Infinite Program", "semi-infinite program")
# But keep "Semi-Infinite Program" in titles if any. Wait, the prompt says "Use capitalization only in titles or named methods."
# Since I just replaced all, let's fix the title just in case.
text = text.replace("semi-infinite programming", "semi-infinite programming") # just making sure grammar is ok

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
