using Pkg
Pkg.activate(normpath(joinpath(@__DIR__)))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, JuMP, HiGHS, OSQP
include(joinpath(@__DIR__, "src", "RobustSIP.jl"))
using .RobustSIP

df = CSV.read("data/processed_state_return_pairs.csv", DataFrame)
returns_cols = names(df)[2:31]
X_all = Matrix{Float64}(df[2:end, returns_cols])

t_start = (161 - 1) * 21 + 1  # 161 is where it gets stuck after printing 160
t_end = t_start + 1260 - 1
X_train = X_all[t_start:t_end, :]

mu = vec(mean(X_train, dims=1)) .* 252.0
cov_mat = cov(X_train) .* 252.0
target_return = mean(mu)
max_weight = 0.15

println("Running HiGHS...")
solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=HiGHS.Optimizer)
println("Running OSQP...")
solve_min_variance(cov_mat, mu, target_return, max_weight; optimizer=OSQP.Optimizer)
println("Done.")
