using Pkg
Pkg.activate(".")
using CSV, DataFrames, Statistics, LinearAlgebra
include("RobustSIP.jl")
using .RobustSIP

output_dir = "../results"
X_all_df = CSV.read("../data/aligned_market_data.csv", DataFrame)
X_all = Matrix(X_all_df[!, 2:31])
Y_all = Matrix(X_all_df[!, ["logVIX", "Drawdown"]])

tau = 0.05
max_weight = 0.15

window_id = 100
t_start = 2100
X_sub = X_all[t_start : t_start + 1260 - 1, :]
Y_sub = Y_all[t_start : t_start + 1260 - 1, :]
mu_sub = mean(X_sub, dims=1)[:] * 252.0
t_ret_sub = median(mu_sub)

v_min_s, v_max_s = extrema(Y_sub[:, 1])
d_min_s, d_max_s = extrema(Y_sub[:, 2])
dv_s = 0.10 * (v_max_s - v_min_s)
dd_s = 0.10 * (d_max_s - d_min_s)
v_bnds = (v_min_s - dv_s, v_max_s + dv_s)
d_bnds = (max(0.0, d_min_s - dd_s), min(1.0, d_max_s + dd_s))

sig_v, sig_d = std(Y_sub[:, 1]), std(Y_sub[:, 2])
H_sub = [(sig_v * 1260^(-1/6))^2 0.0; 0.0 (sig_d * 1260^(-1/6))^2]

# Adaptive SIP on 21x21 grid
vg21 = range(v_bnds[1], v_bnds[2], length=21)
dg21 = range(d_bnds[1], d_bnds[2], length=21)
grid21 = [[v, d] for v in vg21 for d in dg21]

t0_ad = time()
w_ad, lb_ad, ub_ad, act_ad, hist_ad, diag_ad, final_gap_ad, stop_reason_ad, clamping_ad = solve_robust_sip(X_sub, Y_sub, grid21, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0; max_iter=15, max_weight=max_weight)
t_ad = time() - t0_ad

# Dense LP on 21x21 (441 states)
t0_d21 = time()
w_d21, val_d21, diag_d21 = solve_master_cvar(X_sub, Y_sub, grid21, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0, max_weight)
t_d21 = time() - t0_d21
l1_ad_d21 = ismissing(w_d21) ? missing : sum(abs.(w_ad - w_d21))

# Dense LP on 41x41 (1681 states)
vg41 = range(v_bnds[1], v_bnds[2], length=41)
dg41 = range(d_bnds[1], d_bnds[2], length=41)
grid41 = [[v, d] for v in vg41 for d in dg41]

t0_d41 = time()
w_d41, val_d41, diag_d41 = solve_master_cvar(X_sub, Y_sub, grid41, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0, max_weight)
t_d41 = time() - t0_d41
l1_ad_d41 = ismissing(w_d41) ? missing : sum(abs.(w_ad - w_d41))

# Dispersion calculation
vol_cov = cov(X_sub)
L_rho = max_weight * sqrt(tr(vol_cov)) / (tau * sqrt(det(H_sub)))
delta_v = step(vg41)
delta_d = step(dg41)
rho = sqrt(delta_v^2 + delta_d^2) / 2.0

grid_df = DataFrame(
    Method=["Adaptive SIP (21x21 oracle)", "Dense Grid (21x21, 441 states)", "Dense Grid (41x41, 1681 states)"],
    Termination_Status=[diag_ad.Termination_Status, diag_d21.Termination_Status, diag_d41.Termination_Status],
    Primal_Status=[diag_ad.Primal_Status, diag_d21.Primal_Status, diag_d41.Primal_Status],
    Dual_Status=[diag_ad.Dual_Status, diag_d21.Dual_Status, diag_d41.Dual_Status],
    Has_Primal_Solution=[diag_ad.Has_Primal_Solution, diag_d21.Has_Primal_Solution, diag_d41.Has_Primal_Solution],
    Active_States=[length(act_ad), length(grid21), length(grid41)],
    Runtime_sec=[t_ad, t_d21, t_d41],
    Objective_Value=[diag_ad.Objective_Value, diag_d21.Objective_Value, diag_d41.Objective_Value],
    Objective_Bound=[diag_ad.Objective_Bound, diag_d21.Objective_Bound, diag_d41.Objective_Bound],
    Absolute_Gap=[diag_ad.Absolute_Gap, diag_d21.Absolute_Gap, diag_d41.Absolute_Gap],
    Relative_Gap=[diag_ad.Relative_Gap, diag_d21.Relative_Gap, diag_d41.Relative_Gap],
    Exchange_Residual=[final_gap_ad, missing, missing],
    Exchange_Stop_Reason=[stop_reason_ad, missing, missing],
    Distance_to_Adaptive=[0.0, l1_ad_d21, l1_ad_d41],
    Distance_to_Dense21=[l1_ad_d21, 0.0, (ismissing(w_d21) || ismissing(w_d41)) ? missing : sum(abs.(w_d21 - w_d41))],
    Dispersion_Radius_rho=[rho*2, rho*2, rho]
)
CSV.write(joinpath(output_dir, "grid_comparison.csv"), grid_df)

open(joinpath(output_dir, "grid_validation.txt"), "w") do f
    write(f, "=== Robust SIP Computational and Empirical Validation Summary ===\n\n")
    write(f, "Representative Window Benchmark:\n")
    write(f, "  Adaptive SIP solve time: $(round(t_ad, digits=4)) s (Active States: $(length(act_ad)))\n")
    write(f, "  Dense Grid 21x21 solve time: $(round(t_d21, digits=4)) s, L1 dist to Adaptive: $(ismissing(l1_ad_d21) ? "missing" : round(l1_ad_d21, digits=6))\n")
    write(f, "  Dense Grid 41x41 solve time: $(round(t_d41, digits=4)) s, L1 dist to Adaptive: $(ismissing(l1_ad_d41) ? "missing" : round(l1_ad_d41, digits=6))\n")
    write(f, "  Spatial Dispersion Radius rho (21x21): $(round(rho*2, digits=4))\n")
end

println("Done")
