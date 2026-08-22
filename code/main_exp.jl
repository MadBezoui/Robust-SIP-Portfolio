println("Starting Robust SIP Portfolio Reproduction Pipeline")

include("01_run_backtest.jl")
include("02_evaluate_performance.jl")
include("03_statistical_inference.jl")

println("\n--- Step 1: Rolling Backtest ---")
run_backtest()

println("\n--- Step 2: Performance Evaluation ---")
evaluate_backtest(0.0010, 0.05)

println("\n--- Step 3: Statistical Inference ---")
run_statistical_inference()

println("\n--- Step 4: Figure Generation ---")
run(`python3 generate_publication_figures.py`)

println("\nPipeline complete.")
