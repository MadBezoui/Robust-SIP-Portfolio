using DataFrames, CSV, Statistics

df = CSV.read("results/strategy_holding_period_returns.csv", DataFrame)

r1 = df.RobustSIP_Ret
r2 = df.MinVar_Ret

println(length(r1))
println(length(r2))

s1 = (mean(r1) / std(r1)) * sqrt(12.0)
s2 = (mean(skipmissing(r2)) / std(skipmissing(r2))) * sqrt(12.0)

println("SR Robust:", s1)
println("SR MinVar:", s2)
println("Diff: ", s1 - s2)
