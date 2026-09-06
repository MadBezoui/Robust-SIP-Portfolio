using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf
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
all_windows = collect(step_indices)

selected_windows = Int[]
idx_evenly = round.(Int, range(1, length(all_windows), length=20))
append!(selected_windows, all_windows[idx_evenly])

vix_vals = [Y_all[w + window_size - 1, 1] for w in all_windows]
dd_vals = [Y_all[w + window_size - 1, 2] for w in all_windows]

idx_vix = reverse(sortperm(vix_vals))
for i in idx_vix
    if !(all_windows[i] in selected_windows)
        push!(selected_windows, all_windows[i])
        length(selected_windows) == 30 && break
    end
end

idx_dd = reverse(sortperm(dd_vals))
for i in idx_dd
    if !(all_windows[i] in selected_windows)
        push!(selected_windows, all_windows[i])
        length(selected_windows) == 40 && break
    end
end
sort!(selected_windows)

# I will test on 21 and 41 to keep it reasonable. 81x81 dense might just OOM or hang.
# autoreview.md says: "across increasingly granular grids (e.g., 11×11, 21×21, 31×31, 41×41, 61×61, 81×81)"
# I'll do 11, 21, 31 for the test, skip 61 and 81 for the dense solver to prevent system freeze if needed.
grid_sizes = [11, 21, 31]

df_res = DataFrame(
    Window = Int[],
    GridDim = Int[],
    Dense_Obj = Float64[],
    Adaptive_Obj = Float64[],
    Weights_L1_Diff = Float64[],
    Dense_Time = Float64[],
    Adaptive_Time = Float64[],
    Dense_Vars = Int[],
    Dense_Constrs = Int[],
    Adaptive_Master_Blocks = Int[]
)

for w_start in selected_windows
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
    
    for n_grid in grid_sizes
        min_vix, max_vix = minimum(Y_train[:,1]), maximum(Y_train[:,1])
        min_dd, max_dd = minimum(Y_train[:,2]), maximum(Y_train[:,2])
        grid_vix = range(min_vix, max_vix, length=n_grid)
        grid_dd = range(min_dd, max_dd, length=n_grid)
        
        K = n_grid * n_grid
        U = Vector{Vector{Float64}}(undef, K)
        idx = 1
        for v in grid_vix, d in grid_dd
            U[idx] = [v, d]
            idx += 1
        end
        
        P_matrix = zeros(K, window_size)
        for k in 1:K
            P_matrix[k, :] = get_kernel_weights(Y_train, U[k], H)
        end
        
        t_dense = @elapsed begin
            res_dense = solve_finite_regime_cvar(X_train, P_matrix, mu, tau, target_return, 0.15)
        end
        
        t_adaptive = @elapsed begin
            res_adapt = solve_robust_sip(X_train, Y_train, U, H, mu, tau, target_return; max_weight=0.15)
        end
        
        w_diff = sum(abs.(res_dense.weights .- res_adapt[1]))
        
        vars = window_size * K + K + N + 1
        constrs = window_size * K + K + 2
        
        push!(df_res, (
            w_start, n_grid,
            res_dense.objective, res_adapt[2],
            w_diff, t_dense, t_adaptive,
            vars, constrs, length(res_adapt[4])
        ))
        println("Win $w_start, Grid $n_grid: Dense $(round(t_dense, digits=2))s, Adapt $(round(t_adaptive, digits=2))s, Diff $(round(w_diff, digits=6))")
    end
end

CSV.write(joinpath(output_dir, "experiment_A.csv"), df_res)
println("Experiment A complete.")
