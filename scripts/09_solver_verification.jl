using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, JuMP, HiGHS, Clarabel
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
max_weight = 0.15

step_indices = 1:step_size:(T_total - window_size - step_size + 1)
total_steps = length(step_indices)

df_results = DataFrame(
    Window = Int[],
    Date = Date[],
    HiGHS_Status = String[],
    Clarabel_Status = String[],
    HiGHS_Time = Float64[],
    Clarabel_Time = Float64[],
    HiGHS_Obj = Float64[],
    Clarabel_Obj = Float64[],
    Obj_Diff = Float64[],
    Weights_L1_Diff = Float64[],
    Is_Match = Bool[]
)

step_count = 0
for t_start in step_indices
    global step_count += 1
    t_end = t_start + window_size - 1
    
    X_train = X_all[t_start:t_end, :]
    mu = vec(mean(X_train, dims=1))
    cov_mat = cov(X_train)
    target_return = mean(mu)
    
    local res_highs, res_clarabel
    t_highs = @elapsed begin
        res_highs = solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=HiGHS.Optimizer)
    end
    t_clarabel = @elapsed begin
        res_clarabel = solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=Clarabel.Optimizer)
    end
    
    obj_highs = ismissing(res_highs.objective) ? NaN : res_highs.objective
    obj_clarabel = ismissing(res_clarabel.objective) ? NaN : res_clarabel.objective
    
    if ismissing(res_highs.weights[1]) || ismissing(res_clarabel.weights[1])
        obj_diff = NaN
        w_diff = NaN
        is_match = false
    else
        obj_diff = abs(obj_highs - obj_clarabel)
        w_diff = sum(abs.(res_highs.weights .- res_clarabel.weights))
        is_match = obj_diff < 1e-4 && w_diff < 1e-3
    end
    
    push!(df_results, (
        step_count, dates_all[t_end],
        string(res_highs.termination_status), string(res_clarabel.termination_status),
        t_highs, t_clarabel,
        obj_highs, obj_clarabel,
        obj_diff, w_diff, is_match
    ))
end

CSV.write(joinpath(output_dir, "solver_verification.csv"), df_results)
matches = sum(df_results.Is_Match)
println("Solver verification complete. Matches: $matches / $total_steps")
