# Full reproduction of every number in the manuscript.
#
# Run from the `code/` directory:
#
#     julia reproduce_all.jl
#
# Expect several hours. 01_run_backtest.jl alone takes about three hours, and
# each of the four rolling experiments that re-solve the robust SIP costs
# roughly one backtest pass per specification. data_prep.py downloads the two
# public source series (Kenneth French 30 Industry Portfolios, CBOE VIX), so it
# needs network access; every later step runs offline from code/data.

using Pkg
Pkg.activate(@__DIR__)
Pkg.instantiate()

println("=== ROBUST SIP PORTFOLIO REPRODUCTION ===")

# Baseline pipeline: data, backtest, evaluation, inference.
baseline = [
    "scripts/data_prep.py",
    "scripts/01_run_backtest.jl",
    "scripts/02_evaluate_performance.jl",
    "scripts/03_statistical_inference.jl",
]

# Diagnostics and the matched dense-versus-exchange scalability study.
diagnostics = [
    "scripts/run_sensitivity.jl",
    "scripts/run_ess_backtest.jl",
    "scripts/04_experiment_A_matched_dense_vs_adaptive.jl",
    "scripts/05_experiment_B_support_diagnostics.jl",
    "scripts/06_experiment_C_alternative_domains.jl",
    "scripts/07_experiment_F_conditional_downside.jl",
    "scripts/08_experiment_D_net_wealth.jl",
    "scripts/09_solver_verification.jl",
    "scripts/gap_verification.jl",
]

# Revision experiments, each on the identical 377-window calendar as the
# baseline. These produce the tables in Sections 8.2 and 9.
revision = [
    "scripts/run_referee_benchmarks.jl",   # hull-restricted SIP, state-conditioned CVaR
    "scripts/run_domain_sensitivity.jl",   # state-domain margin, delta in {0,5,10,20}%
    "scripts/run_target_sensitivity.jl",   # return target: non-binding, Q25, Q50, Q75
    "scripts/run_shrinkage_benchmark.jl",  # regularized conditional CVaR, 5 lambdas
    "scripts/run_bandwidth_geometry.jl",   # diagonal versus full-covariance bandwidth
    "scripts/run_riskfree_sensitivity.py", # Sharpe at rf = 0, 2, 4 percent
]

# Figures, then the cell-by-cell cross-check of the manuscript against results.
finalize = [
    "scripts/generate_publication_figures.py",
]

for s in vcat(baseline, diagnostics, revision, finalize)
    println("\n>>> Running $s")
    if endswith(s, ".py")
        run(Cmd(`python3 $s`, dir=@__DIR__))
    else
        run(Cmd(`julia --project=$(@__DIR__) $s`, dir=@__DIR__))
    end
end

# The manuscript source lives one level up, in soumission/.
manuscript = normpath(joinpath(@__DIR__, "..", "soumission"))
println("\n>>> Cross-checking the manuscript against the regenerated results")
run(Cmd(`python3 scripts/validate_manuscript.py --tex $(joinpath(manuscript, "main_paper.tex"))`,
        dir=@__DIR__))

println("\n>>> Recompiling the manuscript")
for cmd in (`pdflatex -interaction=nonstopmode main_paper.tex`,
            `bibtex main_paper`,
            `pdflatex -interaction=nonstopmode main_paper.tex`,
            `pdflatex -interaction=nonstopmode main_paper.tex`)
    run(Cmd(cmd, dir=manuscript))
end

println("\nDone. Results in code/results, manuscript in soumission/main_paper.pdf.")
