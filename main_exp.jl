println("Starting Robust SIP Portfolio Reproduction Pipeline")

println("\n--- Step 1: Rolling Backtest ---")
run(`julia --project=. scripts/01_run_backtest.jl`)

println("\n--- Step 2: Performance Evaluation ---")
run(`julia --project=. scripts/02_evaluate_performance.jl`)

println("\n--- Step 3: Statistical Inference ---")
run(`julia --project=. scripts/03_statistical_inference.jl`)

println("\n--- Step 4: Figure Generation ---")
run(`python3 scripts/generate_publication_figures.py`)

println("\nPipeline complete.")
