# ==============================================================================
# main_exp.jl
# 
# Master script to reproduce the complete empirical pipeline.
# ==============================================================================

println("Starting Robust SIP Portfolio Backtest and Evaluation Pipeline")

println("\n--- Step 1: Run Backtest ---")
include("01_run_backtest.jl")
run_full_backtest(0.05, 1260, 21, 21, 21)

println("\n--- Step 2: Evaluate Performance ---")
include("02_evaluate_performance.jl")
evaluate_backtest(0.0010, 0.05)

println("\n--- Step 3: Run Sensitivity Analysis ---")
include("run_sensitivity.jl")

println("\n--- Step 4: Statistical Inference ---")
include("03_statistical_inference.jl")

println("\n--- Step 5: Generate Publication Figures ---")
run(`python3 generate_publication_figures.py`)

println("\nPipeline complete. All results and figures are saved in the `results/` directory.")
