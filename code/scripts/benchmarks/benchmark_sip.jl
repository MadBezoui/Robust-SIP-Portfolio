using Pkg
Pkg.activate("/Users/madanibezoui/Documents/Projects/Robust_Portfolio/Portfolio_Robust_SIP_RealData/code")
using LinearAlgebra, Statistics, Dates, DataFrames, CSV, JuMP, HiGHS

include("RobustSIP.jl")
using .RobustSIP

data_path = "/Users/madanibezoui/Documents/Projects/Robust_Portfolio/Portfolio_Robust_SIP_RealData/data/aligned_market_data.csv"
df = CSV.read(data_path, DataFrame)
X_raw = Matrix{Float64}(df[:, 2:31]) ./ 100.0
Y_raw = Matrix{Float64}(df[:, 32:33])
N = 30

X_train = X_raw[1:1260, :]
Y_train = Y_raw[1:1260, :]
mu_train = mean(X_train, dims=1)[:] * 252.0
cov_train = cov(X_train) * 252.0

sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
n_train = size(Y_train, 1)
h_vix = 1.06 * sigma_vix * n_train^(-1/6)
h_dd  = 1.06 * sigma_dd  * n_train^(-1/6)
H = [h_vix^2 0.0; 0.0 h_dd^2]

vix_min, vix_max = extrema(Y_train[:, 1])
dd_min, dd_max = extrema(Y_train[:, 2])
delta_v = 0.10 * (vix_max - vix_min)
delta_d = 0.10 * (dd_max - dd_min)

vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=21)
dd_grid  = range(dd_min - delta_d, dd_max + delta_d, length=21)
grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]

target_return = median(mu_train)
tau = 0.05
max_weight = 0.15

println("Benchmarking RobustSIP on 1 window...")
t0 = time()
w_rob, lb, ub, active_thetas, hist = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=10, max_weight=max_weight)
t_sip = time() - t0
println("RobustSIP solve time: ", round(t_sip, digits=4), " s")
println("Iterations: ", length(hist), ", Active thetas: ", length(active_thetas))
