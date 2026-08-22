with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""(\texttt{code/01\_run\_backtest.jl} and
\texttt{code/02\_evaluate\_performance.jl}): Executes the rolling-window
out-of-sample backtest and generates the performance, transaction-cost,
and bootstrap outputs reported in the manuscript."""

new_text = r"""(\texttt{code/01\_run\_backtest.jl}, \texttt{code/02\_evaluate\_performance.jl}, and \texttt{code/03\_statistical\_inference.jl}): Executes the rolling-window
out-of-sample backtest and generates the performance, transaction-cost,
and bootstrap outputs reported in the manuscript."""

text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
