using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Statistics

include(normpath(joinpath(@__DIR__, "..", "scripts", "02_evaluate_performance.jl")))

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
for s in ["CondCVaR", "RobustSIP_Hull"]
    perf = CSV.read(joinpath(output_dir, "perf_$(s).csv"), DataFrame)
    weights = CSV.read(joinpath(output_dir, "weights_$(s).csv"), DataFrame)
    
    r_net = perf.Return
    turnovers = perf.Turnover
    w_mat = Matrix(weights[:, 2:end])
    
    m = calculate_metrics(r_net, w_mat, turnovers, 0.0010)
    
    # ann_mean, ann_vol, sharpe, sortino, cvar_95_holding, cvar_99_holding, max_dd, cagr, calmar, avg_turnover, tc_drag, eff_n, worst_period, wealth[end]
    println(s, " & ", round(m[1]*100, digits=2), " & ", round(m[2]*100, digits=2), " & ", round(m[3], digits=2), " & ", round(m[4], digits=2), " & ", round(m[7]*100, digits=2), " & ", round(m[10]*100, digits=2), " & ", round(m[12], digits=1), " & ", round(m[14], digits=2), " \\\\")
end
