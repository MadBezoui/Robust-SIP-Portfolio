using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra
include(joinpath(@__DIR__, "..", "src", "RobustSIP.jl"))
using .RobustSIP

data_path = normpath(joinpath(@__DIR__, "..", "data", "processed_state_return_pairs.csv"))
output_dir = normpath(joinpath(@__DIR__, "..", "results"))
mkpath(output_dir)

df = CSV.read(data_path, DataFrame)
returns_cols = names(df)[2:31]
X_all = Matrix{Float64}(df[:, returns_cols])
dates_all = df.Date
T_total, N = size(X_all)
window_size = 1260
step_size = 21
step_indices = 1:step_size:(T_total - window_size - step_size + 1)

domains = [
    ("alt1_ret_vix", ["MarketEWReturn", "logVIX"]),
    ("alt2_dd_rf", ["Drawdown63", "RiskFreeReturn"]),
    ("alt3_ret_dd", ["MarketEWReturn", "Drawdown63"])
]

for (name, cols) in domains
    println("Running backtest for alternative domain: $name ($cols)")
    Y_raw = Matrix{Float64}(df[:, cols])
    X_train_all = X_all[2:end, :]
    Y_train_all = Y_raw[1:end-1, :]
    
    df_w = DataFrame(Window=Int[], Date=Date[])
    for c in returns_cols
        df_w[!, Symbol(c)] = Float64[]
    end
    
    for (i, w_start) in enumerate(step_indices)
        w_end = w_start + window_size - 1
        X_train = X_train_all[w_start:w_end, :]
        Y_train = Y_train_all[w_start:w_end, :]
        
        mu = vec(mean(X_train, dims=1))
        target_return = mean(mu)
        tau = 0.05
        c_bw = 1.0
        
        H_plugin = cov(Y_train)
        det_H = det(H_plugin)
        if det_H < 1e-12
            H_plugin = H_plugin + 1e-6 * I
        end
        H = c_bw * (window_size^(-1/3)) * H_plugin
        
        min_1, max_1 = minimum(Y_train[:,1]), maximum(Y_train[:,1])
        min_2, max_2 = minimum(Y_train[:,2]), maximum(Y_train[:,2])
        n_grid = 21
        grid_1 = range(min_1, max_1, length=n_grid)
        grid_2 = range(min_2, max_2, length=n_grid)
        
        K = n_grid * n_grid
        U = Vector{Vector{Float64}}(undef, K)
        idx = 1
        for v in grid_1, d in grid_2
            U[idx] = [v, d]
            idx += 1
        end
        
        res = solve_robust_sip(X_train, Y_train, U, H, mu, tau, target_return; max_weight=0.15)
        
        w_out = ismissing(res[1]) ? fill(NaN, N) : res[1]
        
        push!(df_w, vcat([i, dates_all[w_end+1]], w_out))
        if i % 50 == 0; println("  Window $i / $(length(step_indices)) completed."); end
    end
    CSV.write(joinpath(output_dir, "weights_RobustSIP_$name.csv"), df_w)
end

println("Experiment C complete.")
