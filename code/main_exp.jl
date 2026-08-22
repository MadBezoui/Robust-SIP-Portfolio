println("Starting Robust SIP Portfolio Backtest and Evaluation Pipeline")

println("\n--- Step 4: Statistical Inference ---")
include("03_statistical_inference.jl")
run_bootstrap_inference()

println("\n--- Step 5: Generate Publication Figures ---")
run(`python3 generate_publication_figures.py`)

println("\nPipeline complete. All results and figures are saved in the results/ directory.")
