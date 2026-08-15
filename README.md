# Adaptive exchange for robust continuous-state portfolio selection

This repository contains the complete reproducible codebase, historical datasets, numerical tables, and generated publication figures for the research paper: **"From market states to robust portfolios: grid-restricted adaptive CVaR optimization with real financial data"** by Madani Bezoui and Thiziri Sifaoui.

## Abstract
Portfolio risk depends heavily on prevailing macroeconomic conditions, yet standard robust portfolio optimization models frequently represent those conditions through a rigid discrete set of regimes. We introduce a data-driven semi-infinite portfolio optimization framework in which every point of a continuous market-state space induces a conditional empirical return distribution. Market states are characterized by observable financial indicators (VIX and equity market drawdown), and multivariate kernel weights connect historical observations to any continuous target state. Portfolio risk is measured by the worst-case conditional value-at-risk (CVaR) over a compact continuous state space. We solve the resulting semi-infinite program efficiently using an adaptive exchange algorithm that alternates between a finite master linear program and a continuous-state oracle.

## Repository structure

- `code/`: Contains the complete Julia and Python source code.
  - `RobustSIP.jl`: Core library implementing the Adaptive Semi-Infinite Programming (SIP) exchange algorithm, the finite master LP solver, the continuous separation oracle, and the finite-regime CVaR baseline.
  - `main_exp.jl`: The rolling-window backtest pipeline over 30 years comparing Robust SIP against 1/N, MinVar, Nominal CVaR, and Finite-Regime CVaR, including the unstudentized paired circular block bootstrap test and sensitivity analyses.
  - `data_prep.py`: Python script for acquiring and cleaning Kenneth French 30 Industry Portfolios and CBOE VIX data.
- `data/`: Contains the aligned daily financial dataset (`aligned_market_data.csv`).
- `figures/`: Contains the generated analytical figures (PDF) and summary numerical tables (CSV).
  - `performance_table.csv`: 14 summary statistics across all strategies net of 10 bps transaction costs.
  - `crisis_performance.csv`: Sub-sample return and drawdown metrics across Dot-Com, GFC, COVID-19, and 2022 inflation periods.
  - `bootstrap_inference.csv`: Unstudentized paired circular block bootstrap Sharpe ratio difference inference.
  - `grid_validation.txt`: Computational diagnostic comparisons against dense grid discretization.
  - 10 analytical PDF plots (wealth trajectory, drawdowns, weights, turnover, active states, bounds, efficient frontier, kernel density map, and bootstrap distribution).
- `paper/`: Contains the full LaTeX manuscript (`main_paper.tex`), bibliography (`references.bib`), TikZ schemas, and the compiled manuscript (`main_paper.pdf`).

## Reproduction instructions

To reproduce the exact empirical results and figures presented in the paper, execute the following command in Julia:

```bash
cd code
julia main_exp.jl
```

The script will execute the rolling-window backtest, perform the exchange optimizations, run the unstudentized paired circular block bootstrap, and export all figures and CSV tables directly into `figures/`.

To compile the LaTeX paper:

```bash
cd paper
pdflatex main_paper.tex
bibtex main_paper
pdflatex main_paper.tex
pdflatex main_paper.tex
```

## Authors
- **Madani Bezoui** (1st author and corresponding author), CESI LINEACT, Nancy, France
- **Thiziri Sifaoui** (2nd author), University of Tamanghasset and LAROMAD, UMMTO, Algeria
