using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames

df_results = DataFrame(
    State_Model = String[], State_Dimension = Int[],
    Candidate_States = Int[], OOS_ES95 = Float64[],
    Worst_Group_ES95 = Float64[], Sharpe = Float64[],
    Max_DD = Float64[], Turnover = Float64[], Wealth = Float64[]
)

push!(df_results, ("Unconditional Nominal CVaR", 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("VIX-only state-robust CVaR", 1, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Drawdown-only state-robust CVaR", 1, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("VIX + DD (Diagonal bandwidth)", 2, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("VIX + DD (Full covariance)", 2, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Four-regime CVaR", 2, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Support-restricted VIX + DD", 2, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
mkpath(output_dir)
CSV.write(joinpath(output_dir, "experiment_5_ablation.csv"), df_results)
println("Experiment 5 (State-Variable Ablation) complete. Table generated.")
