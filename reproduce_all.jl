using Pkg
Pkg.activate(".")
Pkg.instantiate()

println("=== ROBUST SIP PORTFOLIO REPRODUCTION SCRIPT ===")
println("Starting full reproduction. This will take some time.")

scripts = [
    "scripts/data_prep.py",
    "scripts/01_run_backtest.jl",
    "scripts/04_experiment_A_matched_dense_vs_adaptive.jl",
    "scripts/05_experiment_B_support_diagnostics.jl",
    "scripts/06_experiment_C_alternative_domains.jl",
    "scripts/07_experiment_F_conditional_downside.jl",
    "scripts/09_solver_verification.jl"
]

for s in scripts
    println("\n>>> Running $s")
    if endswith(s, ".py")
        run(`python3 $s`)
    else
        run(`julia --project=. $s`)
    end
end

println("\n=== ALL EXPERIMENTS COMPLETED SUCCESSFULLY ===")
