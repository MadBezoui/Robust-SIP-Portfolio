with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

s1 = """master solves. The exact counting convention should be stated explicitly,
because an algorithm that starts with one state and subsequently adds
$m-1$ states may report either $m$ master solves or $m-1$ exchange updates."""

r1 = """master solves. We report the number of master-LP solves. Under the one-state initialization and one-new-state-per-update rule, a converged run with $m$ final active states entails $m$ master-LP solves and $m-1$ state-addition updates."""

text = text.replace(s1, r1)

s2 = """corresponding to an observed runtime
ratio of approximately 16.2 under the reported hardware, software, and
implementation conditions (under the reported HiGHS 1.24.1 configuration \cite{highs2022}, tolerance $10^{-4}$) over dense LP discretization"""

r2 = """corresponding to an observed runtime ratio of
\\[
72.7093/4.4851\\approx16.21
\\]
relative to the dense $21\\times21$ extensive-form implementation on the representative benchmark window. This ratio is instance- and implementation-specific and is not a general complexity bound, under the reported hardware, software, and
implementation conditions (under the reported HiGHS 1.24.1 configuration \cite{highs2022}, tolerance $10^{-4}$)"""

text = text.replace(s2, r2)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
