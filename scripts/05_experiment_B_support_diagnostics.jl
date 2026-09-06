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
Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown63"]])
dates_all = df.Date

T_total, N = size(X_all)
window_size = 1260
step_size = 21

step_indices = 1:step_size:(T_total - window_size - step_size + 1)
total_steps = length(step_indices)

df_res = DataFrame(
    Window = Int[],
    Date = Date[],
    StateIdx = Int[],
    logVIX = Float64[],
    Drawdown63 = Float64[],
    Total_Prob = Float64[],
    ESS = Float64[],
    Tail_ESS = Float64[],
    Min_Euclidean_Dist = Float64[],
    In_Convex_Hull = Bool[]
)

for w_start in step_indices
    w_end = w_start + window_size - 1
    X_train = X_all[w_start:w_end, :]
    Y_train = Y_all[w_start:w_end, :]
    
    mu = vec(mean(X_train, dims=1))
    target_return = mean(mu)
    tau = 0.05
    c = 1.0
    
    H_plugin = cov(Y_train)
    det_H = det(H_plugin)
    if det_H < 1e-12
        H_plugin = H_plugin + 1e-6 * I
    end
    H = c * (window_size^(-1/3)) * H_plugin
    
    min_vix, max_vix = minimum(Y_train[:,1]), maximum(Y_train[:,1])
    min_dd, max_dd = minimum(Y_train[:,2]), maximum(Y_train[:,2])
    n_grid = 21
    grid_vix = range(min_vix, max_vix, length=n_grid)
    grid_dd = range(min_dd, max_dd, length=n_grid)
    
    K = n_grid * n_grid
    U = Vector{Vector{Float64}}(undef, K)
    idx = 1
    for v in grid_vix, d in grid_dd
        U[idx] = [v, d]
        idx += 1
    end
    
    res = solve_robust_sip(X_train, Y_train, U, H, mu, tau, target_return; max_weight=0.15)
    weights = res[1]
    active_states = res[4]
    
    if ismissing(weights) || length(weights) == 0 || ismissing(weights[1])
        continue
    end
    
    # Calculate support diagnostics for binding active states
    for i in 1:length(active_states)
        theta = active_states[i]
        s = findfirst(x -> x == theta, U)
        if s === nothing; s = -1; end
        p = get_kernel_weights(Y_train, theta, H)
        ess = effective_sample_size(p)
        t_ess = tail_specific_ess(weights, X_train, p, tau)
        
        dists = [norm(Y_train[t, :] - theta) for t in 1:window_size]
        min_dist = minimum(dists)
        in_hull = is_in_convex_hull(theta, Y_train)
        
        push!(df_res, (
            w_start, dates_all[w_end], s,
            theta[1], theta[2],
            sum(p), ess, t_ess, min_dist, in_hull
        ))
    end
    println("Window $w_start / $(step_indices[end]) completed.")
end

CSV.write(joinpath(output_dir, "worst_state_support.csv"), df_res)
println("Experiment B complete.")
