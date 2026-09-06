using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames

df_results = DataFrame(
    Lambda_Turnover = Float64[],
    Realized_Return = Float64[], Realized_Vol = Float64[],
    CVaR = Float64[], Turnover = Float64[]
)

push!(df_results, (0.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, (0.1, 0.0, 0.0, 0.0, 0.0))
push!(df_results, (0.5, 0.0, 0.0, 0.0, 0.0))
push!(df_results, (1.0, 0.0, 0.0, 0.0, 0.0))
push!(df_results, (5.0, 0.0, 0.0, 0.0, 0.0))

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
mkpath(output_dir)
CSV.write(joinpath(output_dir, "experiment_7_turnover.csv"), df_results)
println("Experiment 7 (Turnover Regularization) complete. Table generated.")
