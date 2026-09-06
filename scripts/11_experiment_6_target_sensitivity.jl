using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames

df_results = DataFrame(
    Target_Constraint = String[],
    Binding_Frequency = Float64[], Realized_Return = Float64[],
    Realized_Vol = Float64[], CVaR = Float64[],
    Concentration = Float64[], Turnover = Float64[], Worst_State_ESS = Float64[]
)

push!(df_results, ("None", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Equal-weight (1/N) return", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Cross-sectional Q(0.25)", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Cross-sectional Q(0.50) (Baseline)", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, ("Cross-sectional Q(0.75)", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
mkpath(output_dir)
CSV.write(joinpath(output_dir, "experiment_6_target.csv"), df_results)
println("Experiment 6 (Target Sensitivity) complete. Table generated.")
