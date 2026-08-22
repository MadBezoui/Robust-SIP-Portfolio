using CSV, DataFrames, Printf
include("ledoit_wolf.jl")

df = CSV.read("results/strategy_holding_period_returns.csv", DataFrame)
dropmissing!(df)
rob_ret = Float64.(df[:, "RobustSIP_Ret"])
benchmarks = ["1/N", "MinVar", "NominalCVaR", "FiniteRegime"]

println("=== TABLE 8: Primary Bootstrap (b=12) ===")
for bench in benchmarks
    b_ret = Float64.(df[:, bench * "_Ret"])
    diff, se, ci_l, ci_u, p_val = lw_studentized_bootstrap(rob_ret, b_ret, 12, 5000; seed=2026)
    @printf("%s & %.4f & %.4f & [%.4f, %.4f] & %.3f \\\\\n", bench, diff, se, ci_l, ci_u, p_val)
end
println()

println("=== TABLE 13: Block-Length Sensitivity (vs NominalCVaR) ===")
nom_ret = Float64.(df[:, "NominalCVaR_Ret"])
for b in [6, 9, 12, 15, 18, 21, 24]
    diff, se, ci_l, ci_u, p_val = lw_studentized_bootstrap(rob_ret, nom_ret, b, 5000; seed=2026)
    @printf("%d & %.4f & %.4f & [%.4f, %.4f] & %.3f \\\\\n", b, diff, se, ci_l, ci_u, p_val)
end
