using LinearAlgebra, Statistics, Dates, DataFrames, CSV
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
tau = 0.05

function cvar_wrapper(th)
    cvar, _ = RobustSIP.conditional_cvar(w, X, Y, th, H, tau)
    return cvar
end

grad_analytical = RobustSIP.grad_cvar_theta(w, theta, X, Y, H, tau)

eps = 1e-6
c_base = cvar_wrapper(theta)
grad_fd = zeros(2)
for i in 1:2
    th_plus = copy(theta)
    th_plus[i] += eps
    c_plus = cvar_wrapper(th_plus)
    
    th_minus = copy(theta)
    th_minus[i] -= eps
    c_minus = cvar_wrapper(th_minus)
    
    grad_fd[i] = (c_plus - c_minus) / (2 * eps)
end

println("Analytical: ", grad_analytical)
println("FD:         ", grad_fd)
println("Difference: ", norm(grad_analytical - grad_fd))
@assert norm(grad_analytical - grad_fd) < 1e-4 "Gradient test failed!"
println("Finite difference validation passed for the production gradient.")
