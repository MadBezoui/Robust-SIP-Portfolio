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
tau = 0.05
max_weight = 0.15
c = 1.0

# 20 evenly spaced windows
windows_idx = round.(Int, range(1, stop=(T_total - window_size + 1), length=20))

println("Running 1001x1001 gap verification over 20 windows...")
global max_gap = 0.0

for t_start in windows_idx
    t_end = t_start + window_size - 1
    X_train = X_all[t_start:t_end, :]
    Y_train = Y_all[t_start:t_end, :]
    
    mu_train = mean(X_train, dims=1)[:] * 252.0
    mu_max = min(sum(sort(mu_train, rev=true)[1:5]) / 5, maximum(mu_train))
    target_return = mu_max * 0.5
    
    std_v = std(Y_train[:, 1])
    std_d = std(Y_train[:, 2])
    H = (size(Y_train, 1)^(-1/3)) * [ (c * std_v)^2 0.0 ; 0.0 (c * std_d)^2 ]
    
    v_range = (minimum(Y_train[:,1]) - 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])), maximum(Y_train[:,1]) + 0.1*(maximum(Y_train[:,1])-minimum(Y_train[:,1])))
    d_range = (0.0, maximum(Y_train[:,2]) + 0.1*maximum(Y_train[:,2]))
    
    v_grid_21 = range(v_range[1], v_range[2], length=21)
    d_grid_21 = range(d_range[1], d_range[2], length=21)
    candidate_thetas = vec([[v, d] for v in v_grid_21, d in d_grid_21])
    w_star, val_21, st = solve_robust_sip(X_train, Y_train, candidate_thetas, H, mu_train, tau, target_return; max_weight=max_weight)
    
    if !ismissing(w_star)
        v_grid_dense = range(v_range[1], v_range[2], length=1001)
        d_grid_dense = range(d_range[1], d_range[2], length=1001)
        
        losses = -(X_train * w_star)
        sorted_idx = sortperm(losses, rev=true)
        sorted_losses = losses[sorted_idx]
        
        H_inv = inv(H)
        
        max_dense_cvar = -Inf
        
        # O(T) inner loop with pre-allocated buffer
        T = size(X_train, 1)
        u_buffer = zeros(2)
        
        for v in v_grid_dense
            for d in d_grid_dense
                # Fast kernel weights
                max_log = -Inf
                for t in 1:T
                    u_buffer[1] = Y_train[t, 1] - v
                    u_buffer[2] = Y_train[t, 2] - d
                    lw = -0.5 * (u_buffer[1]^2 * H_inv[1,1] + u_buffer[2]^2 * H_inv[2,2]) # assuming diagonal H
                    if lw > max_log
                        max_log = lw
                    end
                end
                
                sum_W = 0.0
                for t in 1:T
                    u_buffer[1] = Y_train[t, 1] - v
                    u_buffer[2] = Y_train[t, 2] - d
                    lw = -0.5 * (u_buffer[1]^2 * H_inv[1,1] + u_buffer[2]^2 * H_inv[2,2])
                    sum_W += exp(lw - max_log)
                end
                
                cvar_val = 0.0
                cum_p = 0.0
                for i in 1:T
                    t_orig = sorted_idx[i]
                    u_buffer[1] = Y_train[t_orig, 1] - v
                    u_buffer[2] = Y_train[t_orig, 2] - d
                    lw = -0.5 * (u_buffer[1]^2 * H_inv[1,1] + u_buffer[2]^2 * H_inv[2,2])
                    p_i = exp(lw - max_log) / sum_W
                    
                    if cum_p + p_i <= tau
                        cvar_val += (p_i / tau) * sorted_losses[i]
                        cum_p += p_i
                    else
                        rem = tau - cum_p
                        cvar_val += (rem / tau) * sorted_losses[i]
                        break
                    end
                end
                
                if cvar_val > max_dense_cvar
                    max_dense_cvar = cvar_val
                end
            end
        end
        
        gap = max_dense_cvar - val_21
        if gap > max_gap
            global max_gap = gap
        end
        println("Window \$t_start: 21x21 CVaR = \$val_21, 1001x1001 CVaR = \$max_dense_cvar, Gap = \$gap")
    end
end
open(normpath(joinpath(@__DIR__, "..", "results", "gap_dense.txt")), "w") do f
    write(f, string(max_gap))
end
println("Max Gap across 20 windows: ", max_gap)
