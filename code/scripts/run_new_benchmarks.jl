using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Statistics, LinearAlgebra, Printf

include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

# 1. Load Data
data_path = normpath(joinpath(@__DIR__, "..", "data", "aligned_market_data.csv"))
df = CSV.read(data_path, DataFrame)

col_names = names(df)
vix_idx = findfirst(x -> x == "VIX", col_names)
returns_cols = col_names[2:(vix_idx - 1)]

X_raw = Matrix{Float64}(df[:, returns_cols])
Y_raw = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])

X_all = X_raw[2:end, :]
Y_all = Y_raw[1:end-1, :]

T_total, N = size(X_all)

# Parameters
window_size = 252
holding_period = 21
tau = 0.05
max_weight = 0.15 # In 01_run_backtest.jl it is 0.15!
c = 1.0
E_min = 0.0

out_cond = DataFrame(vcat(:Date => String[], Symbol.(returns_cols) .=> Ref(Float64[])))
out_hull = DataFrame(vcat(:Date => String[], Symbol.(returns_cols) .=> Ref(Float64[])))

println("Running $(length(1:holding_period:(T_total - window_size - holding_period + 1))) windows...")

for t_start in 1:holding_period:(T_total - window_size - holding_period + 1)
    t_end = t_start + window_size - 1
    
    X_train = X_all[t_start:t_end, :]
    Y_train = Y_all[t_start:t_end, :]
    
    mu_train = mean(X_train, dims=1)[:] * 252.0
    mu_max = min(sum(sort(mu_train, rev=true)[1:5]) / 5, maximum(mu_train))
    target_return = mu_max * 0.5
    
    std_v = std(Y_train[:, 1])
    std_d = std(Y_train[:, 2])
    H = (window_size^(-1/3)) * [ (c * std_v)^2 0.0 ; 0.0 (c * std_d)^2 ]
    
    # Current state
    theta_current = Y_train[end, :]
    
    # CondCVaR
    w_cond, val, st = solve_conditional_cvar(X_train, Y_train, theta_current, H, mu_train, tau, target_return, max_weight)
    
    # RobustSIP_Hull
    # Build full grid
    v_range = (minimum(Y_train[:,1]) - 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])), maximum(Y_train[:,1]) + 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])))
    d_range = (0.0, maximum(Y_train[:,2]) + 0.1*maximum(Y_train[:,2]))
    v_grid = range(v_range[1], v_range[2], length=21)
    d_grid = range(d_range[1], d_range[2], length=21)
    
    candidate_thetas = [ [v, d] for v in v_grid, d in d_grid ]
    candidate_thetas = vec(candidate_thetas)
    filtered_grid = filter_grid_to_hull(candidate_thetas, Y_train)
    
    if isempty(filtered_grid)
        filtered_grid = candidate_thetas
    end
    
    w_hull, val_hull, st_hull = solve_robust_sip(X_train, Y_train, filtered_grid, H, mu_train, tau, target_return; max_weight=max_weight)
    
    rebal_date = string(df[t_end + 1, "Date"]) # Because X_all is shifted by 1
    
    if !ismissing(w_cond)
        push!(out_cond, Tuple(vcat(rebal_date, w_cond)))
    else
        push!(out_cond, Tuple(vcat(rebal_date, fill(1.0/N, N))))
    end
    
    if !ismissing(w_hull)
        push!(out_hull, Tuple(vcat(rebal_date, w_hull)))
    else
        push!(out_hull, Tuple(vcat(rebal_date, fill(1.0/N, N))))
    end
end

CSV.write(normpath(joinpath(@__DIR__, "..", "results", "weights_CondCVaR.csv")), out_cond)
CSV.write(normpath(joinpath(@__DIR__, "..", "results", "weights_RobustSIP_Hull.csv")), out_hull)

println("Done computing new benchmarks.")
