using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, JuMP, HiGHS, OSQP
include(joinpath(@__DIR__, "..", "src", "RobustSIP.jl"))
using .RobustSIP

data_path = normpath(joinpath(@__DIR__, "..", "data", "processed_state_return_pairs.csv"))
output_dir = normpath(joinpath(@__DIR__, "..", "results"))
mkpath(output_dir)

df = CSV.read(data_path, DataFrame)
returns_cols = names(df)[2:31]

X_all = Matrix{Float64}(df[2:end, returns_cols])
dates_all = df.Date

T_total, N = size(X_all)
window_size = 1260
step_size = 21
max_weight = 0.15

step_indices = 1:step_size:(T_total - window_size - step_size + 1)
total_steps = length(step_indices)

df_results = DataFrame(
    Window = Int[], Date = Date[],
    HiGHS_Status = String[], Alt_Status = String[],
    HiGHS_Time = Float64[], Alt_Time = Float64[],
    HiGHS_Obj = Float64[], Alt_Obj = Float64[],
    Obj_Diff = Float64[], Weights_L1_Diff = Float64[], Is_Match = Bool[]
)

step_count = 0
for t_start in step_indices
    global step_count += 1
    t_end = t_start + window_size - 1
    X_train = X_all[t_start:t_end, :]
    mu = vec(mean(X_train, dims=1)) .* 252.0
    cov_mat = cov(X_train) .* 252.0
    target_return = mean(mu)
    
    local res_highs, res_alt
    t_highs = @elapsed res_highs = solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=HiGHS.Optimizer)
    
    t_alt = @elapsed res_alt = solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=OSQP.Optimizer)
    
    obj_highs = ismissing(res_highs.objective) ? NaN : res_highs.objective
    obj_alt = ismissing(res_alt.objective) ? NaN : res_alt.objective
    
    if ismissing(res_highs.weights[1]) || ismissing(res_alt.weights[1])
        obj_diff = NaN
        w_diff = NaN
        is_match = false
    else
        obj_diff = abs(obj_highs - obj_alt)
        w_diff = sum(abs.(res_highs.weights .- res_alt.weights))
        is_match = obj_diff < 1e-4 && w_diff < 1e-3
    end
    
    push!(df_results, (step_count, dates_all[t_end], string(res_highs.termination_status), string(res_alt.termination_status), t_highs, t_alt, obj_highs, obj_alt, obj_diff, w_diff, is_match))
    if step_count % 10 == 0
        println("Processed $step_count / $total_steps windows...")
    end
end

CSV.write(joinpath(output_dir, "solver_verification.csv"), df_results)
matches = sum(df_results.Is_Match)
println("Solver verification complete. Matches: $matches / $total_steps")
