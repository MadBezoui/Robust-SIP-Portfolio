# Continuous-State Robust CVaR Portfolio Optimization via Grid-Restricted Constraint Generation

[![Julia](https://img.shields.io/badge/Julia-1.11+-9558B2?logo=julia&logoColor=white)](https://julialang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21957758.svg)](https://doi.org/10.5281/zenodo.21957758)

Official open-source reproducibility repository for the paper:  
**"Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation"**  
by **Madani Bezoui** and **Thiziri Sifaoui** (*Computational Optimization and Applications*, 2026).

---

## Overview

Portfolio risk depends critically on prevailing financial-market conditions. Standard robust portfolio optimization models typically approximate these dynamics through discrete regime-switching models or static uncertainty sets. 

This repository implements a **continuous-state robust portfolio optimization framework**:
1. **Continuous Market-State Space**: Market conditions are represented in a continuous 2D state space $\Theta$ parameterized by observable macro-financial state variables: **log-VIX** (market volatility/fear gauge) and **trailing equity drawdown** (crisis stress).
2. **Conditional Kernel Density Return Distributions**: Multivariate Nadaraya-Watson kernel smoothing maps historical observations to any target state $\theta \in \Theta$, generating state-conditional asset return distributions.
3. **Continuous-State Semi-Infinite Program (SIP)**: We formulate the robust Conditional Value-at-Risk (CVaR) optimization as a semi-infinite program with infinitely many state-dependent CVaR constraints.
4. **Adaptive Exchange Algorithm**: The continuous SIP is solved efficiently via an adaptive grid-restricted constraint generation algorithm alternating between a finite master Linear Program (LP) and an active-constraint separation oracle.

---

## Repository Structure

```
Robust-SIP-Portfolio/
├── Project.toml                     # Julia project definition & dependencies
├── Manifest.toml                    # Exact reproducible dependency lockfile
├── LICENSE                          # MIT License
├── CITATION.cff                     # Citation Metadata Format (CFF)
├── README.md                        # Documentation and replication guide
├── main_exp.jl                      # Master pipeline entry point
│
├── src/                             # Core library source code
│   └── RobustSIP.jl                 # Adaptive SIP solver, master LP, separation oracle & baselines
│
├── scripts/                         # Execution & analysis scripts
│   ├── 01_run_backtest.jl           # 30-year rolling-window out-of-sample backtest (1995-2026)
│   ├── 02_evaluate_performance.jl   # 14 out-of-sample performance metrics & sub-period crisis analysis
│   ├── 03_statistical_inference.jl  # Paired circular block bootstrap inference for Sharpe differences
│   ├── run_sensitivity.jl           # Grid resolution, bandwidth, ESS & block length sensitivity analyses
│   ├── generate_publication_figures.py # Generates publication-ready figures (PDF)
│   ├── data_prep.py                 # Acquisition and alignment script (Kenneth French 30 & VIX)
│   ├── data_prep.jl                 # Julia alternative for dataset extraction
│   ├── validate_manuscript.py       # Numerical verification and consistency checks
│   ├── run_ess_backtest.jl          # Full rolling backtest across ESS regularizations
│   └── benchmarks/                  # Performance benchmarks and verification tests
│
├── data/                            # Empirical datasets
│   └── aligned_market_data.csv      # Aligned daily/monthly asset returns and state indicators
│
└── results/                         # Empirical outputs and publication figures
    ├── performance_table.csv        # 14 summary statistics across strategies (10 bps TC)
    ├── crisis_performance.csv       # Crisis metrics: Dot-Com, GFC, COVID-19, 2022 Inflation
    ├── bootstrap_inference.csv      # Paired circular block bootstrap p-values and CIs
    ├── active_states_history.csv    # Oracle active-state history across rolling windows
    ├── grid_sensitivity.csv         # Discretization grid resolution sensitivity
    ├── bandwidth_sensitivity.csv    # Kernel bandwidth multiplier sensitivity
    ├── ess_sensitivity.csv          # Effective Sample Size (ESS) regularization sensitivity
    ├── block_length_sensitivity.csv # Block bootstrap window length robustness
    └── *.pdf                        # High-resolution analytical publication figures
```

---

## Software Requirements

- **Julia 1.11+**
  - Standard packages: `JuMP.jl` (v1.29+), `HiGHS.jl` (v1.20+), `DataFrames.jl`, `CSV.jl`, `Distributions.jl`, `StatsBase.jl`
- **Python 3.9+** (for figure generation)
  - `matplotlib`, `pandas`, `numpy`

---

## Quick Start & Reproduction

### 1. Environment Setup

Clone the repository and instantiate the locked Julia environment:

```bash
git clone https://github.com/MadBezoui/Robust-SIP-Portfolio.git
cd Robust-SIP-Portfolio
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Install Python dependencies for plotting:

```bash
pip install matplotlib pandas numpy
```

### 2. Full Replication in One Command

To run the complete end-to-end pipeline (rolling backtests, 14 performance metrics, paired block bootstrap tests, and publication figure generation):

```bash
julia --project=. main_exp.jl
```

All outputs (CSVs and publication PDFs) will be written directly into `results/`.

---

## Running Individual Components

Each script can also be executed independently from the repository root:

- **Rolling Backtest**:
  ```bash
  julia --project=. scripts/01_run_backtest.jl
  ```
  Runs the 377 monthly rolling out-of-sample windows (1995–2026) across 5 strategies:
  - **Robust SIP** (proposed continuous-state framework)
  - **Finite-Regime CVaR** (discrete-regime baseline)
  - **Nominal CVaR** (unconditional Rockafellar-Uryasev model)
  - **TC-MinVar** (target-constrained minimum variance)
  - **1/N** (equal-weighted benchmark)

- **Performance & Crisis Evaluation**:
  ```bash
  julia --project=. scripts/02_evaluate_performance.jl
  ```
  Computes 14 institutional performance metrics (Annualized Return, Volatility, Sharpe, Sortino, Realized Holding CVaR 95/99%, Max Drawdown, CAGR, Calmar, Turnover, Transaction Cost Drag, Effective N) and sub-period crisis returns (Dot-Com crash, Global Financial Crisis, COVID shock, 2022 Inflation).

- **Statistical Significance**:
  ```bash
  julia --project=. scripts/03_statistical_inference.jl
  ```
  Computes the circular moving-block bootstrap ($B = 5\,000$ resamples) for pairwise Sharpe ratio differences with block length sensitivity.

- **Generate Publication Figures**:
  ```bash
  python3 scripts/generate_publication_figures.py
  ```
  Renders all publication figures (wealth trajectories, drawdown curves, asset allocation weights, active state counts, kernel maps, efficient frontiers, and bootstrap distributions).

- **Sensitivity Analysis**:
  ```bash
  julia --project=. scripts/run_sensitivity.jl
  ```

---

## Citation

If you use this code, data, or algorithm in your research, please cite:

```bibtex
@article{bezoui2026robust,
  title   = {Continuous-state robust {CVaR} portfolio optimization via grid-restricted constraint generation},
  author  = {Bezoui, Madani and Sifaoui, Thiziri},
  journal = {Computational Optimization and Applications},
  year    = {2026},
  doi     = {10.5281/zenodo.21957758},
  url     = {https://github.com/MadBezoui/Robust-SIP-Portfolio}
}
```

Or reference `CITATION.cff`.

---

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
