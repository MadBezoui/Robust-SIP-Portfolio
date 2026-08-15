using Pkg
Pkg.activate("/Users/madanibezoui/Documents/Projects/Robust_Portfolio/Portfolio_Robust_SIP_RealData/code")
using LinearAlgebra, Statistics, Dates, DataFrames, CSV, JuMP, HiGHS

println("Testing vectorized kernel calculation...")
Y_test = randn(1260, 2)
vix_grid = range(10.0, 50.0, length=21)
dd_grid = range(0.0, 0.5, length=21)
grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]

# Fast vectorized kernel matrix for all 441 states at once:
h_vix, h_dd = 5.0, 0.05
thetas_mat = hcat(grid_thetas...) # 2 x 441
diff_vix = (Y_test[:, 1] .- thetas_mat[1, :]') ./ h_vix # 1260 x 441
diff_dd  = (Y_test[:, 2] .- thetas_mat[2, :]') ./ h_dd  # 1260 x 441
D = diff_vix.^2 .+ diff_dd.^2 # 1260 x 441
log_w = -0.5 .* D
max_log = maximum(log_w, dims=1)
W = exp.(log_w .- max_log)
P_all = W ./ sum(W, dims=1) # 1260 x 441

println("Vectorized kernel weights shape: ", size(P_all))
println("Time for 441 states: instantaneous!")
