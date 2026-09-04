using Pkg
Pkg.activate("/Users/madanibezoui/Documents/Projects/Robust_Portfolio/Portfolio_Robust_SIP_RealData/code")
using LinearAlgebra, Statistics, Dates, DataFrames, CSV, JuMP, HiGHS

data_path = "/Users/madanibezoui/Documents/Projects/Robust_Portfolio/Portfolio_Robust_SIP_RealData/data/aligned_market_data.csv"
df = CSV.read(data_path, DataFrame)
X_raw = Matrix{Float64}(df[:, 2:31]) ./ 100.0
Y_raw = Matrix{Float64}(df[:, 32:33])
N = 30

X_train = X_raw[1:1260, :]
mu_train = mean(X_train, dims=1)[:] * 252.0
cov_train = cov(X_train) * 252.0
cov_psd = cov_train + 1e-4 * I

println("Testing fast QP solve...")
t0 = time()
model = Model(HiGHS.Optimizer)
set_silent(model)
set_attribute(model, "time_limit", 1.0)
@variable(model, 0 <= w[1:N] <= 0.15)
@constraint(model, sum(w) == 1.0)
@constraint(model, dot(mu_train, w) >= median(mu_train))
@objective(model, Min, dot(w, cov_psd * w))
optimize!(model)
t_qp = time() - t0
println("Time with 1.0s limit and 1e-4 ridge: ", round(t_qp, digits=4), " s, status: ", termination_status(model))
