using Pkg
Pkg.activate(normpath(joinpath(@__DIR__)))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, JuMP, HiGHS, OSQP
include(joinpath(@__DIR__, "src", "RobustSIP.jl"))
using .RobustSIP

df = CSV.read("data/processed_state_return_pairs.csv", DataFrame)
X = Matrix{Float64}(df[1:1260, 2:31])
mu = vec(mean(X, dims=1))
cov_mat = cov(X)

println("Running HiGHS...")
@time solve_min_variance(cov_mat, mu, mean(mu), 0.15; optimizer=HiGHS.Optimizer)
println("Running OSQP...")
@time solve_min_variance(cov_mat, mu, mean(mu), 0.15; optimizer=OSQP.Optimizer)
println("Done.")
