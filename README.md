# Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation

This repository contains the complete reproducible codebase, historical datasets, numerical tables, and generated publication figures for the research paper: **"Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation"** by Madani Bezoui and Thiziri Sifaoui.

## Abstract
Portfolio risk depends heavily on prevailing financial-market conditions, yet standard robust portfolio optimization models frequently represent those conditions through a rigid discrete set of regimes. We introduce a continuous-state robust portfolio optimization framework in which every point of a continuous market-state space induces a conditional empirical return distribution. Market states are characterized by observable financial indicators (log-VIX and equity market drawdown), and multivariate kernel weights connect historical observations to any target state. The paper formulates a continuous-state SIP and implements a finite grid-restricted approximation solved through adaptive constraint generation. We solve the resulting grid-restricted program efficiently using an adaptive exchange algorithm that alternates between a finite master linear program and a grid-restricted separation oracle.

## Repository structure

- `code/`: Contains the complete Julia and Python source code.
  - `RobustSIP.jl`: Core library implementing the Adaptive Semi-Infinite Programming (SIP) exchange algorithm, the finite master LP solver, the grid-restricted separation oracle, and the finite-regime CVaR baseline.
  - `main_exp.jl`: The rolling-window backtest pipeline over 30 years comparing Robust SIP against 1/N, Target-Constrained MinVar (TC-MinVar), Nominal CVaR, and Finite-Regime CVaR, including the unstudentized paired circular block bootstrap test.
  - `run_sensitivity.jl`: Script generating sensitivity experiments for grid resolution, kernel bandwidth, ESS regularization, and bootstrap block length.
  - `data_prep.py`: Python script for acquiring and cleaning Kenneth French 30 Industry Portfolios and CBOE VIX data.
  - `generate_publication_figures.py`: Script generating all publication-quality figures directly from empirical outputs.
- `data/`: Contains the aligned daily financial dataset (`aligned_market_data.csv`).
- `results/`: Contains the generated analytical figures (PDF) and summary numerical tables (CSV).
  - `performance_table.csv`: 14 summary statistics across all strategies net of 10 bps transaction costs.
  - `crisis_performance.csv`: Sub-sample return and drawdown metrics across Dot-Com, GFC, COVID-19, and 2022 inflation periods.
  - `bootstrap_inference.csv`: Unstudentized paired circular block bootstrap Sharpe ratio difference inference.
  - `grid_sensitivity.csv`, `bandwidth_sensitivity.csv`, `ess_sensitivity.csv`, `ess_full_backtest.csv`, `block_length_sensitivity.csv`: Output data for all sensitivity experiments.
  - 10 analytical PDF plots (wealth trajectory, drawdowns, weights, turnover, active states, bounds, efficient frontier, kernel density map, and bootstrap distribution).

## Release Information
The exact code and results corresponding to this manuscript are available under the versioned GitHub tag **v1.1.0** (commit `4a73dcb1b9e2c827f3f3f2eaf79ed5b2a58eea74`). A matching Zenodo archive will be cited upon availability.
- **GitHub Tag:** [v1.1.0](https://github.com/MadBezoui/Robust-SIP-Portfolio/tree/v1.1.0)

## Software Environment
Computations were validated on an Apple M1 Pro using Julia 1.11.6, CSV 0.10.16, DataFrames 1.8.2, JuMP 1.31.1, and HiGHS 1.24.1.

## Reproduction instructions

To reproduce the exact empirical results and figures presented in the paper, execute the following commands in your terminal:

```bash
cd code
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. main_exp.jl
```

The script will execute the rolling-window backtest, perform the exchange optimizations, run the unstudentized paired circular block bootstrap, and export all results and CSV tables directly into `results/`.

## Authors
- **Madani Bezoui** (1st author and corresponding author), CESI LINEACT, Nancy, France
- **Thiziri Sifaoui** (2nd author), University of Tamanghasset and LAROMAD, UMMTO, Algeria
