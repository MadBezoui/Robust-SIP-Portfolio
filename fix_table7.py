with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

# Just use string replace for exactly the chunk
old_chunk = r"""Adaptive exchange, $21\times21$ grid & Exchange residual \\
$\le 10^{-4}$ & 5 active state blocks & 4.49 s
& LB $\approx 3.356246\%$, oracle $\approx 3.358510\%$ \\
Dense $21\times 21$ & OPTIMAL & 441 & 72.71 s & optimum $\approx 3.3578\%$ \\
Dense $41\times41$ & Time limit reached; no primal incumbent returned
& 1681 state blocks & 632.25 s & Not available \\"""

new_chunk = r"""Adaptive exchange, $21\times21$ grid & Exchange residual $\le 10^{-4}$ & 5 & 4.49 s & LB $\approx 3.356246\%$, oracle $\approx 3.358510\%$ \\
Dense $21\times 21$ & OPTIMAL & 441 & 72.71 s & optimum $\approx 3.3578\%$ \\
Dense $41\times41$ & Time limit; no primal incumbent & 1681 & 632.25 s & Not available \\"""

if old_chunk in text:
    text = text.replace(old_chunk, new_chunk)
else:
    print("Could not find the chunk")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
