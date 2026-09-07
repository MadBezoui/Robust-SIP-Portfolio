using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Statistics, LinearAlgebra, Printf
include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

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

window_size = 252
holding_period = 21
tau = 0.05
max_weight = 0.15
c = 1.0

# 20 evenly spaced windows
windows_idx = round.(Int, range(1, stop=(T_total - window_size - holding_period + 1), length=20))

lambdas = [0.0, 0.1, 0.5, 1.0, 5.0]

df_results = DataFrame(
    Lambda_Turnover = Float64[],
    Avg_Turnover = Float64[],
    Avg_Return = Float64[]
)

for lam in lambdas
    turnovers = []
    returns = []
    
    # We need a w_prev. For the first step we can just use 1/N.
    # To properly compute turnover we actually need consecutive windows.
    # But since we're jumping, we'll just simulate a 2-period step for each window
    for t_start in windows_idx
        # First window to establish w_prev
        t_end = t_start + window_size - 1
        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        mu_train = mean(X_train, dims=1)[:] * 252.0
        mu_max = min(sum(sort(mu_train, rev=true)[1:5]) / 5, maximum(mu_train))
        t_ret = mu_max * 0.5
        H = (size(Y_train, 1)^(-1/3)) * [ (c * std(Y_train[:,1]))^2 0.0 ; 0.0 (c * std(Y_train[:,2]))^2 ]
        
        v_range = (minimum(Y_train[:,1]) - 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])), maximum(Y_train[:,1]) + 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])))
        d_range = (0.0, maximum(Y_train[:,2]) + 0.1*maximum(Y_train[:,2]))
        candidate_thetas = vec([[v, d] for v in range(v_range[1], v_range[2], length=21), d in range(d_range[1], d_range[2], length=21)])
        
        # Base solve for w_prev
        w_prev, _, _ = solve_robust_sip(X_train, Y_train, candidate_thetas, H, mu_train, tau, t_ret; max_weight=max_weight)
        if ismissing(w_prev)
            w_prev = fill(1.0/N, N)
        end
        
        # Second window
        t_start2 = t_start + holding_period
        t_end2 = t_start2 + window_size - 1
        X_train2 = X_all[t_start2:t_end2, :]
        Y_train2 = Y_all[t_start2:t_end2, :]
        mu_train2 = mean(X_train2, dims=1)[:] * 252.0
        mu_max2 = min(sum(sort(mu_train2, rev=true)[1:5]) / 5, maximum(mu_train2))
        t_ret2 = mu_max2 * 0.5
        H2 = (size(Y_train2, 1)^(-1/3)) * [ (c * std(Y_train2[:,1]))^2 0.0 ; 0.0 (c * std(Y_train2[:,2]))^2 ]
        
        v_range2 = (minimum(Y_train2[:,1]) - 0.1*(maximum(Y_train2[:,1])-minimum(Y_train2[:,1])), maximum(Y_train2[:,1]) + 0.1*(maximum(Y_train2[:,1])-minimum(Y_train2[:,1])))
        d_range2 = (0.0, maximum(Y_train2[:,2]) + 0.1*maximum(Y_train2[:,2]))
        candidate_thetas2 = vec([[v, d] for v in range(v_range2[1], v_range2[2], length=21), d in range(d_range2[1], d_range2[2], length=21)])
        
        # Drift w_prev
        p_ret = prod(1.0 .+ X_all[t_end+1:t_start2-1, :], dims=1)[:]
        w_prev_drifted = (w_prev .* p_ret) ./ sum(w_prev .* p_ret)
        
        # Solve with penalty!
        # wait! solve_robust_sip does not support lambda_turnover yet. I need to modify solve_robust_sip to accept it and pass it to solve_master_cvar_regularized!
        # Ah! I can just use solve_master_cvar_regularized with a fixed active set (e.g. the final active set from lambda=0).
    end
end
        w_base, val_base, st, active_thetas = solve_robust_sip_with_active(X_train2, Y_train2, candidate_thetas2, H2, mu_train2, tau, t_ret2; max_weight=max_weight)
        
        w_reg, _, _ = solve_master_cvar_regularized(X_train2, Y_train2, active_thetas, H2, mu_train2, tau, t_ret2, max_weight, w_prev_drifted, lam)
        if !ismissing(w_reg)
            push!(turnovers, sum(abs.(w_reg .- w_prev_drifted)) / 2.0)
            
            # Period return
            p_ret2 = prod(1.0 .+ X_all[t_end2+1:t_end2+holding_period, :], dims=1)[:]
            push!(returns, sum(w_reg .* p_ret2) - 1.0)
        end
    end
    push!(df_results, (lam, mean(turnovers), mean(returns)*12.0))
end
CSV.write(normpath(joinpath(@__DIR__, "..", "results", "experiment_7_turnover_regularization.csv")), df_results)
println(df_results)
