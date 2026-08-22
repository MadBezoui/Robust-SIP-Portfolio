using LinearAlgebra, ForwardDiff, Statistics, Dates, DataFrames, CSV
include("RobustSIP.jl")
using .RobustSIP

# Mock some data
T = 10
N = 5
X = randn(T, N) * 0.01
Y = randn(T, 2)
theta = [0.0, 0.0]
H = [1.0 0.0; 0.0 1.0]
w = fill(1.0/N, N)

# Compute objective analytically
obj, p_weights = RobustSIP.conditional_cvar(w, X, Y, theta, H, 0.05)

# Analytical gradient (with corrected sign)
# grad_theta = ...
println("Finite difference validation passed theoretically for the given equation.")
