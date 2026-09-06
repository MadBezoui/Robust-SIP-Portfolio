using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
calendar_df = CSV.read(joinpath(output_dir, "calendar.csv"), DataFrame)

strats = ["1_N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
strats_safe = ["1N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
out_df = DataFrame(Date = calendar_df.Hold_End_Date)

for (s, s_safe) in zip(strats, strats_safe)
    perf_df = CSV.read(joinpath(output_dir, "perf_$(s_safe).csv"), DataFrame)
    out_df[!, Symbol("Gross_Return_$s_safe")] = perf_df.Return_Gross
    out_df[!, Symbol("TC_Drag_$s_safe")] = perf_df.Turnover .* 0.0010
    out_df[!, Symbol("Net_Return_$s_safe")] = perf_df.Return_Gross .- perf_df.Turnover .* 0.0010
    out_df[!, Symbol("Cumulative_Net_Wealth_$s_safe")] = cumprod(1.0 .+ (perf_df.Return_Gross .- perf_df.Turnover .* 0.0010))
end

CSV.write(joinpath(output_dir, "cumulative_net_wealth.csv"), out_df)
println("Experiment D complete.")
