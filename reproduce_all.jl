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
    "scripts/08_experiment_D_net_wealth.jl",
    "scripts/09_solver_verification.jl",
    "scripts/10_experiment_4_kernel_bandwidth.jl",
    "scripts/11_experiment_6_target_sensitivity.jl",
    "scripts/12_experiment_7_turnover_regularization.jl",
    "scripts/13_experiment_5_ablation.jl",
    "scripts/patch_manuscript.py"
]

for s in scripts
    println("\n>>> Running $s")
    if endswith(s, ".py")
        run(`python3 $s`)
    else
        run(`julia --project=. $s`)
    end
end

println("\n>>> Recompiling LaTeX Manuscript")
run(Cmd(`pdflatex -interaction=nonstopmode main_paper.tex`, dir="Soumission"))

println("\n=== ALL EXPERIMENTS COMPLETED SUCCESSFULLY ===")
