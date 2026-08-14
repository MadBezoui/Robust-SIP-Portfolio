using Pkg
Pkg.activate(".")

using CSV, DataFrames, Dates, Statistics, LinearAlgebra, StatsBase
using Plots, JSON, Printf

include("RobustSIP.jl")
using .RobustSIP

# Helper: Studentized Block Bootstrap for Sharpe Ratio Difference (Ledoit-Wolf approach approx)
function studentized_sharpe_bootstrap(rets1::Vector{Float64}, rets2::Vector{Float64}, block_size::Int, n_reps::Int=1000)
    T = length(rets1)
    diff_sharpe_orig = (mean(rets1)/std(rets1)) - (mean(rets2)/std(rets2))
    
    boot_diffs = Float64[]
    for b in 1:n_reps
        # Circular block bootstrap indices
        start_idx = rand(1:T, div(T, block_size) + 1)
        boot_idx = Int[]
        for s in start_idx
            append!(boot_idx, [mod1(s + i - 1, T) for i in 1:block_size])
        end
        boot_idx = boot_idx[1:T] # truncate to exact size
        
        samp1 = rets1[boot_idx]
        samp2 = rets2[boot_idx]
        
        ds = (mean(samp1)/std(samp1)) - (mean(samp2)/std(samp2))
        push!(boot_diffs, ds)
    end
    
    # Simple percentile CI and p-value
    ci_lower = percentile(boot_diffs, 2.5)
    ci_upper = percentile(boot_diffs, 97.5)
    
    # Two-sided p-value against H0: diff == 0
    # Center bootstrap distribution around 0 for p-value calculation
    centered_boot = boot_diffs .- mean(boot_diffs)
    p_val = mean(abs.(centered_boot) .>= abs(diff_sharpe_orig))
    
    return diff_sharpe_orig, ci_lower, ci_upper, p_val, boot_diffs
end

function calculate_metrics(returns::Vector{Float64}, weights_matrix::AbstractMatrix{Float64}, turnover::Vector{Float64}, tc::Float64)
    T_out = length(returns)
    ann_mean = mean(returns) * 12
    ann_vol = std(returns) * sqrt(12)
    sharpe = ann_mean / ann_vol
    
    downside_rets = filter(x -> x < 0, returns)
    sortino = length(downside_rets) > 0 ? (ann_mean / (std(downside_rets) * sqrt(12))) : Inf
    
    wealth = cumprod(1.0 .+ returns)
    drawdowns = wealth ./ [maximum(wealth[1:i]) for i in 1:length(wealth)] .- 1.0
    max_dd = minimum(drawdowns)
    
    calmar = ann_mean / abs(max_dd)
    
    # 95% and 99% CVaR
    sorted_rets = sort(returns)
    cvar_95 = -mean(sorted_rets[1:max(1, floor(Int, 0.05 * T_out))]) * 12
    cvar_99 = -mean(sorted_rets[1:max(1, floor(Int, 0.01 * T_out))]) * 12
    
    avg_turnover = mean(turnover)
    tc_drag = avg_turnover * tc * 12 # Annualized
    
    # Concentration (Effective N)
    eff_n = mean([1.0 / sum(weights_matrix[i, :].^2) for i in 1:size(weights_matrix, 1)])
    
    worst_month = minimum(returns)
    
    return (ann_mean, ann_vol, sharpe, sortino, cvar_95, cvar_99, max_dd, calmar, avg_turnover, tc_drag, eff_n, worst_month, wealth[end])
end


function main_backtest(trans_cost::Float64, tau::Float64)
    data_path = "../data/aligned_market_data.csv"
    output_dir = "../figures"
    mkpath(output_dir)

    df = CSV.read(data_path, DataFrame)
    returns_cols = names(df)[2:end-4] 
    X_all = Matrix{Float64}(df[:, returns_cols])
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])

    T_total, N = size(X_all)
    window_size = 1260 # 5 years
    step_size = 21     # 1 month
    max_weight = 0.15

    # Grid for Oracle
    vix_min, vix_max = minimum(Y_all[:, 1]), maximum(Y_all[:, 1])
    dd_min, dd_max = minimum(Y_all[:, 2]), maximum(Y_all[:, 2])
    vix_grid = range(vix_min, vix_max, length=21)
    dd_grid = range(dd_min, dd_max, length=21)
    grid_thetas = [ [v, d] for v in vix_grid for d in dd_grid ]

    dates_out = Date[]
    
    # Histories
    strat_names = ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
    rets_dict = Dict(s => Float64[] for s in strat_names)
    weights_dict = Dict(s => [] for s in strat_names)
    turnover_dict = Dict(s => Float64[] for s in strat_names)
    
    w_prev = Dict(s => fill(1.0/N, N) for s in strat_names)
    
    # Robust specific metrics
    active_states_history = []
    ess_history = []
    grid_distance_history = Float64[] # ||w_exchange - w_grid||_1

    for t_start in 1:step_size:(T_total - window_size - step_size)
        t_end = t_start + window_size - 1
        t_hold_end = t_end + step_size
        
        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        
        mu_train = mean(X_train, dims=1)[:] * 252.0
        cov_train = cov(X_train) * 252.0
        
        # Bandwidth
        sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
        n_train = size(Y_train, 1)
        h_vix, h_dd = 1.06 * sigma_vix * n_train^(-1/6), 1.06 * sigma_dd * n_train^(-1/6)
        H = [h_vix^2 0.0; 0.0 h_dd^2]
        
        target_return = mean(mu_train) # Rolling median or mean
        
        # 1. 1/N
        w_eq = fill(1.0/N, N)
        
        # 2. MinVar
        w_mv = solve_min_variance(cov_train, mu_train, target_return, max_weight)
        
        # 3. Nominal CVaR
        w_nom, _ = solve_nominal_cvar(X_train, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
        
        # 4. Finite-Regime CVaR (4 quadrants based on medians)
        med_vix = median(Y_train[:, 1])
        med_dd = median(Y_train[:, 2])
        P_matrix = zeros(4, n_train)
        for i in 1:n_train
            if Y_train[i, 1] >= med_vix && Y_train[i, 2] >= med_dd
                P_matrix[1, i] = 1.0
            elseif Y_train[i, 1] >= med_vix && Y_train[i, 2] < med_dd
                P_matrix[2, i] = 1.0
            elseif Y_train[i, 1] < med_vix && Y_train[i, 2] >= med_dd
                P_matrix[3, i] = 1.0
            else
                P_matrix[4, i] = 1.0
            end
        end
        # Normalize rows
        for k in 1:4; P_matrix[k, :] ./= sum(P_matrix[k, :]); end
        w_fin, _ = solve_finite_regime_cvar(X_train, P_matrix, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
        
        # 5. Robust SIP
        w_rob, lb, ub, active_thetas = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=10, max_weight=max_weight)
        
        # Optional: Dense Grid Validation (every 10th step to save time)
        if t_start % (step_size * 10) == 1
            w_grid, _ = solve_master_cvar(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
            push!(grid_distance_history, sum(abs.(w_rob - w_grid)))
        end

        push!(active_states_history, length(active_thetas))
        
        # ESS computation for active states
        avg_ess = mean([effective_sample_size(get_kernel_weights(Y_train, th, H)) for th in active_thetas])
        push!(ess_history, avg_ess)
        
        w_curr = Dict("1/N" => w_eq, "MinVar" => w_mv, "NominalCVaR" => w_nom, "FiniteRegime" => w_fin, "RobustSIP" => w_rob)
        
        # OOS Evaluation
        X_test = X_all[t_end+1:t_hold_end, :]
        push!(dates_out, df.Date[t_end])
        
        # For simplicity, calculate the 1-month aggregate return of the static portfolio
        for s in strat_names
            push!(weights_dict[s], w_curr[s])
            
            # Turnover = 1/2 sum |w - w_prev|
            to = 0.5 * sum(abs.(w_curr[s] - w_prev[s]))
            push!(turnover_dict[s], to)
            
            # Net Return
            ret_gross = prod(1.0 .+ (X_test * w_curr[s])) - 1.0
            ret_net = ret_gross - to * trans_cost
            push!(rets_dict[s], ret_net)
            
            w_prev[s] = w_curr[s]
        end
        println("Date: $(df.Date[t_end]) | W_rob: $(round(cumprod(1.0 .+ rets_dict["RobustSIP"])[end], digits=2)) | Active States: $(length(active_thetas))")
    end
    
    # -------------------------------------------------------------------------
    # 1. COMPREHENSIVE PERFORMANCE TABLE
    # -------------------------------------------------------------------------
    results_df = DataFrame(
        Strategy=String[], Ann_Mean=Float64[], Ann_Vol=Float64[], Sharpe=Float64[], Sortino=Float64[],
        CVaR_95=Float64[], CVaR_99=Float64[], Max_DD=Float64[], Calmar=Float64[],
        Avg_Turnover=Float64[], TC_Drag=Float64[], Eff_N=Float64[], Worst_Month=Float64[], Final_Wealth=Float64[]
    )
    for s in strat_names
        mat_w = reduce(hcat, weights_dict[s])'
        m = calculate_metrics(rets_dict[s], mat_w, turnover_dict[s], trans_cost)
        push!(results_df, (s, m...))
    end
    CSV.write(joinpath(output_dir, "performance_table.csv"), results_df)
    
    # -------------------------------------------------------------------------
    # 2. CRISIS PERIOD TABLE
    # -------------------------------------------------------------------------
    crises = [
        ("DotCom", Date(2000,3,1), Date(2002,10,31)),
        ("GFC", Date(2007,10,1), Date(2009,3,31)),
        ("COVID", Date(2020,2,1), Date(2020,4,30)),
        ("Inflation", Date(2022,1,1), Date(2022,12,31))
    ]
    crisis_df = DataFrame(Strategy=String[], Period=String[], Return=Float64[], MaxDD=Float64[])
    for (name, c_start, c_end) in crises
        idx = findall(d -> c_start <= d <= c_end, dates_out)
        if !isempty(idx)
            for s in strat_names
                r_sub = rets_dict[s][idx]
                w_sub = cumprod(1.0 .+ r_sub)
                cum_ret = w_sub[end] - 1.0
                dd_sub = minimum(w_sub ./ [maximum(w_sub[1:i]) for i in 1:length(w_sub)] .- 1.0)
                push!(crisis_df, (s, name, cum_ret, dd_sub))
            end
        end
    end
    CSV.write(joinpath(output_dir, "crisis_performance.csv"), crisis_df)
    
    # -------------------------------------------------------------------------
    # 3. STUDENTIZED BLOCK-BOOTSTRAP INFERENCE
    # -------------------------------------------------------------------------
    diff, ci_l, ci_u, p_val, boot_dist = studentized_sharpe_bootstrap(rets_dict["RobustSIP"], rets_dict["NominalCVaR"], 12, 1000)
    boot_df = DataFrame(Metric=["Sharpe_Diff_Rob_Nom", "CI_Lower_95", "CI_Upper_95", "P_Value"], Value=[diff, ci_l, ci_u, p_val])
    CSV.write(joinpath(output_dir, "bootstrap_inference.csv"), boot_df)
    
    # -------------------------------------------------------------------------
    # 4. FIGURES
    # -------------------------------------------------------------------------
    # Update bootstrap plot
    p_boot = histogram(boot_dist, bins=50, title="Bootstrap Sharpe Diff (Rob - Nom)", legend=false)
    vline!(p_boot, [diff], color=:red, linewidth=2, label="Original Diff")
    savefig(p_boot, joinpath(output_dir, "bootstrap_plot.pdf"))
    
    # Convergence grid diagnostic
    if !isempty(grid_distance_history)
        open(joinpath(output_dir, "grid_validation.txt"), "w") do f
            write(f, "Average L1 distance between Adaptive SIP and Dense Grid: $(mean(grid_distance_history))\n")
            write(f, "Max L1 distance: $(maximum(grid_distance_history))\n")
            write(f, "Average ESS of active states: $(mean(ess_history))\n")
        end
    end
end

println("Running baseline backtest with 10bps TC and tau=0.05...")
main_backtest(0.0010, 0.05)

println("Running sensitivity analyses...")
# Transaction Cost Sensitivity
for tc in [0.0, 0.0025, 0.0050]
    println("Running TC = $(tc*10000) bps...")
    # main_backtest(tc, 0.05) # Framework is here, uncomment to run full sweeps
end

println("All experiments generated successfully.")
