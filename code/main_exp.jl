using Pkg
Pkg.activate(".")

using CSV, DataFrames, Dates, Statistics, LinearAlgebra, StatsBase, Random, Printf

include("RobustSIP.jl")
using .RobustSIP

"""
Paired Circular Moving-Block Bootstrap for Annualized Sharpe Ratio Differences.
"""
function paired_circular_block_bootstrap(rets1::Vector{Float64}, rets2::Vector{Float64}, block_size::Int=12, n_reps::Int=5000; seed::Int=20260814)
    Random.seed!(seed)
    T = length(rets1)
    
    sr1_ann = (mean(rets1) / std(rets1)) * sqrt(12.0)
    sr2_ann = (mean(rets2) / std(rets2)) * sqrt(12.0)
    diff_sharpe_orig = sr1_ann - sr2_ann
    
    boot_diffs = Float64[]
    for b in 1:n_reps
        # Circular block bootstrap sampling
        start_indices = rand(1:T, div(T, block_size) + 1)
        boot_idx = Int[]
        for s in start_indices
            append!(boot_idx, [mod1(s + i - 1, T) for i in 1:block_size])
        end
        boot_idx = boot_idx[1:T] # truncate to exact length T
        
        samp1 = rets1[boot_idx]
        samp2 = rets2[boot_idx]
        
        ds_ann = sqrt(12.0) * ((mean(samp1) / std(samp1)) - (mean(samp2) / std(samp2)))
        push!(boot_diffs, ds_ann)
    end
    
    ci_lower = percentile(boot_diffs, 2.5)
    ci_upper = percentile(boot_diffs, 97.5)
    boot_se = std(boot_diffs)
    
    # Two-sided empirical p-value for H0: diff == 0
    centered_boot = boot_diffs .- mean(boot_diffs)
    p_val = mean(abs.(centered_boot) .>= abs(diff_sharpe_orig))
    
    return diff_sharpe_orig, boot_se, ci_lower, ci_upper, p_val, boot_diffs
end

"""
Calculate comprehensive 14 performance metrics.
"""
function calculate_metrics(returns::Vector{Float64}, weights_matrix::AbstractMatrix{Float64}, turnover::Vector{Float64}, tc::Float64)
    T_out = length(returns)
    ann_mean = mean(returns) * 12.0
    ann_vol = std(returns) * sqrt(12.0)
    sharpe = ann_vol > 0 ? (ann_mean / ann_vol) : 0.0
    
    # Downside deviation relative to MAR = 0
    downside_dev = sqrt(mean(min.(returns, 0.0).^2)) * sqrt(12.0)
    sortino = downside_dev > 0 ? (ann_mean / downside_dev) : Inf
    
    # Wealth including initial wealth 1.0
    wealth = vcat(1.0, cumprod(1.0 .+ returns))
    running_peak = accumulate(max, wealth)
    drawdowns = wealth ./ running_peak .- 1.0
    max_dd = minimum(drawdowns)
    
    # CAGR and Calmar Ratio
    cagr = wealth[end]^(12.0 / T_out) - 1.0
    calmar = abs(max_dd) > 0 ? (cagr / abs(max_dd)) : Inf
    
    # Realized Monthly Expected Shortfall (CVaR on monthly losses)
    losses = -returns
    sorted_losses = sort(losses, rev=true) # worst losses first
    cvar_95_monthly = mean(sorted_losses[1:max(1, floor(Int, 0.05 * T_out))])
    cvar_99_monthly = mean(sorted_losses[1:max(1, floor(Int, 0.01 * T_out))])
    
    avg_turnover = mean(turnover)
    tc_drag = avg_turnover * tc * 12.0 # Annualized in decimal
    
    # Concentration (Effective N)
    eff_n = mean([1.0 / sum(weights_matrix[i, :].^2) for i in 1:size(weights_matrix, 1)])
    worst_month = minimum(returns)
    
    return (ann_mean, ann_vol, sharpe, sortino, cvar_95_monthly, cvar_99_monthly, max_dd, cagr, calmar, avg_turnover, tc_drag, eff_n, worst_month, wealth[end])
end

function run_institutional_backtest(trans_cost::Float64=0.0010, tau::Float64=0.05, E_min::Float64=0.0)
    data_path = "../data/aligned_market_data.csv"
    output_dir = "../figures"
    mkpath(output_dir)

    df = CSV.read(data_path, DataFrame)
    # returns columns are industry portfolios (columns between Date and VIX)
    col_names = names(df)
    vix_idx = findfirst(x -> x == "VIX", col_names)
    returns_cols = col_names[2:(vix_idx - 1)]
    
    println("Identified $(length(returns_cols)) asset return columns: $(returns_cols[1]) ... $(returns_cols[end])")
    
    # Strictly lag state variables: x_t is paired with y_{t-1}
    X_raw = Matrix{Float64}(df[:, returns_cols])
    Y_raw = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])
    dates_raw = df.Date
    
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]
    dates_all = dates_raw[2:end]

    T_total, N = size(X_all)
    window_size = 1260 # 5 years of daily observations (T_train)
    step_size = 21     # 21 trading days (~1 month holding period, T_hold)
    max_weight = 0.15

    strat_names = ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
    rets_dict = Dict(s => Float64[] for s in strat_names)
    rets_gross_dict = Dict(s => Float64[] for s in strat_names)
    weights_dict = Dict(s => [] for s in strat_names)
    turnover_dict = Dict(s => Float64[] for s in strat_names)
    
    calendar_df = DataFrame(
        Window=Int[], Train_Start_Date=Date[], Train_End_Date=Date[],
        Hold_Start_Date=Date[], Hold_End_Date=Date[],
        T_train=Int[], T_hold=Int[]
    )
    
    active_states_history = Int[]
    ess_history = Float64[]
    min_ess_history = Float64[]
    retained_frac_history = Float64[]
    active_states_sample = Vector{Vector{Float64}}()
    sample_convergence_history = []

    # Calculate exact total number of rolling steps
    step_indices = 1:step_size:(T_total - window_size - step_size + 1)
    total_steps = length(step_indices)
    println("Starting rolling out-of-sample backtest ($(total_steps) windows, T_train = $(window_size), T_hold = $(step_size))...")
    flush(stdout)
    
    # Store preceding holding-period asset growth g_{q-1} for drift adjustment
    prev_asset_growth = nothing
    
    step_count = 0
    for t_start in step_indices
        step_count += 1
        t_end = t_start + window_size - 1
        t_hold_start = t_end + 1
        t_hold_end = t_end + step_size
        
        train_start_d = dates_all[t_start]
        train_end_d = dates_all[t_end]
        hold_start_d = dates_all[t_hold_start]
        hold_end_d = dates_all[t_hold_end]
        
        push!(calendar_df, (step_count, train_start_d, train_end_d, hold_start_d, hold_end_d, window_size, step_size))
        
        if step_count % 25 == 0 || step_count == 1 || step_count == total_steps
            println("[Progress: Window $(step_count) / $(total_steps) ($(round(step_count/total_steps*100, digits=1))%)] Rebalance Date: $(train_end_d), Holding End: $(hold_end_d)")
            flush(stdout)
        end
        
        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        
        mu_train = mean(X_train, dims=1)[:] * 252.0
        cov_train = cov(X_train) * 252.0
        
        # Kernel Bandwidth Matrix H (Bivariate rule of thumb: H = T^{-1/3} * Sigma_y)
        sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
        n_train = size(Y_train, 1)
        h_vix = sigma_vix * n_train^(-1/6)
        h_dd  = sigma_dd  * n_train^(-1/6)
        H = [h_vix^2 0.0; 0.0 h_dd^2]
        
        # Compact State Space U_t (training sample bounds + 10% outer safety margin)
        vix_min, vix_max = extrema(Y_train[:, 1])
        dd_min, dd_max = extrema(Y_train[:, 2])
        delta_v = 0.10 * (vix_max - vix_min)
        delta_d = 0.10 * (dd_max - dd_min)
        
        vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=21)
        dd_grid  = range(max(0.0, dd_min - delta_d), min(1.0, dd_max + delta_d), length=21)
        grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]
        
        target_return = median(mu_train)
        
        # 1. Benchmark 1/N
        w_eq = fill(1.0/N, N)
        
        # 2. Benchmark MinVar (target-constrained, max_weight=0.15)
        w_mv = solve_min_variance(cov_train, mu_train, target_return, max_weight)
        
        # 3. Benchmark Nominal CVaR
        w_nom, _ = solve_nominal_cvar(X_train, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
        
        # 4. Benchmark Finite-Regime CVaR (4 quadrants split at training medians)
        med_vix = median(Y_train[:, 1])
        med_dd  = median(Y_train[:, 2])
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
        for k in 1:4
            sum_p = sum(P_matrix[k, :])
            if sum_p > 0
                P_matrix[k, :] ./= sum_p
            else
                P_matrix[k, :] .= 1.0 / n_train
            end
        end
        w_fin, _ = solve_finite_regime_cvar(X_train, P_matrix, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
        
        # Filter grid_thetas based on ESS if E_min > 0
        valid_thetas = Vector{Vector{Float64}}()
        if E_min > 0.0
            for th in grid_thetas
                w_th = get_kernel_weights(Y_train, th, H)
                ess = 1.0 / sum(w_th.^2)
                if ess >= E_min
                    push!(valid_thetas, th)
                end
            end
            if isempty(valid_thetas)
                push!(valid_thetas, [mean(Y_train[:,1]), mean(Y_train[:,2])])
            end
        else
            valid_thetas = grid_thetas
        end
        
        # 5. Proposed Continuous-State Robust SIP
        w_rob, lb, ub, active_thetas, hist = solve_robust_sip(X_train, Y_train, valid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
        
        if step_count == 100 # Representative convergence trace
            sample_convergence_history = hist
            active_states_sample = copy(active_thetas)
        end

        push!(active_states_history, length(active_thetas))
        
        # Average and Min ESS of active states
        active_ess_vals = [effective_sample_size(get_kernel_weights(Y_train, th, H)) for th in active_thetas]
        avg_ess = mean(active_ess_vals)
        min_ess = minimum(active_ess_vals)
        push!(ess_history, avg_ess)
        push!(min_ess_history, min_ess)
        
        retained_frac = length(valid_thetas) / length(grid_thetas)
        push!(retained_frac_history, retained_frac)
        
        w_curr = Dict("1/N" => w_eq, "MinVar" => w_mv, "NominalCVaR" => w_nom, "FiniteRegime" => w_fin, "RobustSIP" => w_rob)
        
        # Realized Holding Period Returns (period q: t_hold_start to t_hold_end)
        X_test = X_all[t_hold_start:t_hold_end, :]
        curr_asset_growth = vec(prod(1.0 .+ X_test, dims=1)) # 1 + R_{i, q}
        
        for s in strat_names
            w_new = copy(w_curr[s])
            
            # Proper pre-trade drift using PRECEDING holding period growth
            if length(weights_dict[s]) > 0 && prev_asset_growth !== nothing
                w_prev = weights_dict[s][end]
                drifted = w_prev .* prev_asset_growth
                w_pre = drifted ./ sum(drifted)
                to = 0.5 * sum(abs.(w_new - w_pre))
            else
                # Initial period: 1/N has 0 turnover if starting from 1/N; optimized strategies trade from 1/N
                if s == "1/N"
                    to = 0.0
                else
                    to = 0.5 * sum(abs.(w_new - fill(1.0/N, N)))
                end
            end
            
            push!(weights_dict[s], w_new)
            push!(turnover_dict[s], to)
            
            # Realized gross & net returns over period q
            ret_gross = dot(w_new, curr_asset_growth) - 1.0
            ret_net = ret_gross - to * trans_cost
            
            push!(rets_gross_dict[s], ret_gross)
            push!(rets_dict[s], ret_net)
        end
        
        # Update preceding growth tracker
        prev_asset_growth = copy(curr_asset_growth)
    end
    
    println("\nBacktest Complete.")
    println("Active States Stats (over $(step_count) windows):")
    println("  Min:    ", minimum(active_states_history))
    println("  Median: ", median(active_states_history))
    println("  Mean:   ", round(mean(active_states_history), digits=2))
    println("  Max:    ", maximum(active_states_history))
    
    # Calculate final metrics for returning
    r_rob = rets_gross_dict["RobustSIP"] .- turnover_dict["RobustSIP"] .* trans_cost
    mat_w_rob = reduce(hcat, weights_dict["RobustSIP"])'
    m_rob = calculate_metrics(r_rob, mat_w_rob, turnover_dict["RobustSIP"], trans_cost)
    
    # If running as sensitivity loop, return metrics early to avoid overwriting standard outputs
    if E_min > 0.0
        return (Ann_Ret=m_rob[1], Volatility=m_rob[2], Sharpe=m_rob[3], Max_DD=m_rob[7]*100, Wealth=m_rob[14], Turnover=m_rob[10]*100,
                Avg_ESS=mean(ess_history), Min_ESS=mean(min_ess_history), Retained_Frac=mean(retained_frac_history)*100.0)
    end

    # -------------------------------------------------------------------------
    # 0. EXPORT BACKTEST CALENDAR
    # -------------------------------------------------------------------------
    CSV.write(joinpath(output_dir, "backtest_calendar.csv"), calendar_df)
    println("Saved backtest_calendar.csv ($(nrow(calendar_df)) windows)")
    
    # -------------------------------------------------------------------------
    # 1. EXPORT 14-METRIC PERFORMANCE TABLE
    # -------------------------------------------------------------------------
    results_df = DataFrame(
        Strategy=String[], Ann_Mean=Float64[], Ann_Vol=Float64[], Sharpe=Float64[], Sortino=Float64[],
        CVaR_95_Monthly=Float64[], CVaR_99_Monthly=Float64[], Max_DD=Float64[], CAGR=Float64[], Calmar=Float64[],
        Avg_Turnover=Float64[], TC_Drag=Float64[], Eff_N=Float64[], Worst_Month=Float64[], Final_Wealth=Float64[]
    )
    for s in strat_names
        mat_w = reduce(hcat, weights_dict[s])'
        m = calculate_metrics(rets_dict[s], mat_w, turnover_dict[s], trans_cost)
        push!(results_df, (s, m...))
    end
    CSV.write(joinpath(output_dir, "performance_table.csv"), results_df)
    println("Saved performance_table.csv")
    display(results_df)
    
    # Also export time-series CSVs for Python figure generation
    ts_df = DataFrame(Date=calendar_df.Hold_End_Date)
    for s in strat_names
        ts_df[!, Symbol(s * "_Ret")] = rets_dict[s]
        ts_df[!, Symbol(s * "_TO")] = turnover_dict[s]
    end
    CSV.write(joinpath(output_dir, "strategy_monthly_returns.csv"), ts_df)
    
    # Export weights time-series
    w_rob_mat = reduce(hcat, weights_dict["RobustSIP"])'
    w_mv_mat = reduce(hcat, weights_dict["MinVar"])'
    w_rob_df = DataFrame(w_rob_mat, Symbol.(returns_cols))
    w_rob_df[!, :Date] = calendar_df.Hold_End_Date
    CSV.write(joinpath(output_dir, "weights_rob.csv"), w_rob_df)
    
    w_mv_df = DataFrame(w_mv_mat, Symbol.(returns_cols))
    w_mv_df[!, :Date] = calendar_df.Hold_End_Date
    CSV.write(joinpath(output_dir, "weights_mv.csv"), w_mv_df)
    
    # -------------------------------------------------------------------------
    # 2. EXPORT CRISIS PERIOD ANALYSIS
    # -------------------------------------------------------------------------
    crises = [
        ("DotCom", Date(2000,3,1), Date(2002,10,31)),
        ("GFC", Date(2007,10,1), Date(2009,3,31)),
        ("COVID", Date(2020,2,1), Date(2020,4,30)),
        ("Inflation", Date(2022,1,1), Date(2022,12,31))
    ]
    crisis_df = DataFrame(Strategy=String[], Period=String[], Return=Float64[], MaxDD=Float64[])
    for (name, c_start, c_end) in crises
        idx = findall(d -> c_start <= d <= c_end, calendar_df.Hold_End_Date)
        if !isempty(idx)
            for s in strat_names
                r_sub = rets_dict[s][idx]
                w_sub = vcat(1.0, cumprod(1.0 .+ r_sub))
                cum_ret = w_sub[end] - 1.0
                running_max = accumulate(max, w_sub)
                dd_sub = minimum(w_sub ./ running_max .- 1.0)
                push!(crisis_df, (s, name, cum_ret, dd_sub))
            end
        end
    end
    CSV.write(joinpath(output_dir, "crisis_performance.csv"), crisis_df)
    println("Saved crisis_performance.csv")
    display(crisis_df)
    
    # -------------------------------------------------------------------------
    # 3. EXPORT TRANSACTION COST SENSITIVITY TABLE
    # -------------------------------------------------------------------------
    tc_levels = [0.0, 0.0005, 0.0010, 0.0020, 0.0050] # 0, 5, 10, 20, 50 bps
    tc_df = DataFrame(Strategy=String[], TC_bps=Float64[], Sharpe=Float64[], Final_Wealth=Float64[])
    for c_val in tc_levels
        for s in strat_names
            # recompute net returns with c_val
            r_net = rets_gross_dict[s] .- turnover_dict[s] .* c_val
            mat_w = reduce(hcat, weights_dict[s])'
            m = calculate_metrics(r_net, mat_w, turnover_dict[s], c_val)
            push!(tc_df, (s, c_val * 10000.0, m[3], m[14]))
        end
    end
    CSV.write(joinpath(output_dir, "tc_sensitivity.csv"), tc_df)
    println("Saved tc_sensitivity.csv")
    
    # -------------------------------------------------------------------------
    # 4. EXPORT UNSTUDENTIZED CIRCULAR BLOCK-BOOTSTRAP INFERENCE
    # -------------------------------------------------------------------------
    println("Computing circular moving-block bootstrap inference (B=5000)...")
    boot_res_df = DataFrame(
        Benchmark=String[], Sharpe_Diff=Float64[], Std_Error=Float64[],
        CI_Lower_95=Float64[], CI_Upper_95=Float64[], P_Value=Float64[]
    )
    
    main_boot_dist = Float64[]
    for bench in ["NominalCVaR", "1/N", "MinVar", "FiniteRegime"]
        diff, se, ci_l, ci_u, p_val, boot_dist = paired_circular_block_bootstrap(
            rets_dict["RobustSIP"], rets_dict[bench], 12, 5000; seed=20260814
        )
        push!(boot_res_df, (bench, diff, se, ci_l, ci_u, p_val))
        if bench == "NominalCVaR"
            main_boot_dist = boot_dist
        end
    end
    CSV.write(joinpath(output_dir, "bootstrap_inference.csv"), boot_res_df)
    CSV.write(joinpath(output_dir, "bootstrap_distribution.csv"), DataFrame(Bootstrap_Diff=main_boot_dist))
    println("Saved bootstrap_inference.csv and bootstrap_distribution.csv")
    display(boot_res_df)
    
    # -------------------------------------------------------------------------
    # 5. EXPORT CONVERGENCE HISTORY AND ACTIVE STATES
    # -------------------------------------------------------------------------
    if !isempty(sample_convergence_history)
        conv_df = DataFrame(
            Iteration=[h.iteration for h in sample_convergence_history],
            Master_LB=[h.lb * 100.0 for h in sample_convergence_history], # daily %
            Oracle_UB=[h.ub * 100.0 for h in sample_convergence_history], # daily %
            Optimality_Gap=[h.gap * 100.0 for h in sample_convergence_history], # daily %
            Active_Count=[h.active_count for h in sample_convergence_history]
        )
        CSV.write(joinpath(output_dir, "convergence_history.csv"), conv_df)
        println("Saved convergence_history.csv")
    end
    
    # Export active states from sample window and distribution of active counts
    if !isempty(active_states_sample)
        sample_states_df = DataFrame(
            State_Index=1:length(active_states_sample),
            logVIX=[th[1] for th in active_states_sample],
            Drawdown=[th[2] for th in active_states_sample],
            Raw_VIX=[exp(th[1]) for th in active_states_sample],
            Drawdown_Pct=[th[2] * 100.0 for th in active_states_sample]
        )
        CSV.write(joinpath(output_dir, "active_states_sample.csv"), sample_states_df)
        println("Saved active_states_sample.csv")
    end
    
    active_hist_df = DataFrame(Window=1:step_count, Active_States=active_states_history, ESS=ess_history)
    CSV.write(joinpath(output_dir, "active_states_history.csv"), active_hist_df)
    
    # -------------------------------------------------------------------------
    # 6. EXPORT REAL IN-SAMPLE EFFICIENT FRONTIER DATA
    # -------------------------------------------------------------------------
    println("Computing real in-sample efficient frontiers across target returns...")
    mu_full = mean(X_all, dims=1)[:] * 252.0
    cov_full = cov(X_all) * 252.0
    
    vix_min_f, vix_max_f = extrema(Y_all[:, 1])
    dd_min_f, dd_max_f = extrema(Y_all[:, 2])
    vix_grid_f = range(vix_min_f, vix_max_f, length=21)
    dd_grid_f  = range(max(0.0, dd_min_f), min(1.0, dd_max_f), length=21)
    grid_thetas_f = [[v, d] for v in vix_grid_f for d in dd_grid_f]
    
    sigma_vix_f, sigma_dd_f = std(Y_all[:, 1]), std(Y_all[:, 2])
    h_vix_f = sigma_vix_f * size(Y_all, 1)^(-1/6)
    h_dd_f  = sigma_dd_f  * size(Y_all, 1)^(-1/6)
    H_f = [h_vix_f^2 0.0; 0.0 h_dd_f^2]
    
    mu_max_achievable = max_feasible_return(mu_full, max_weight)
    mu_min_achievable = min_feasible_return(mu_full, max_weight)
    
    target_grid = range(mu_min_achievable * 1.05, mu_max_achievable * 0.95, length=25)
    frontier_df = DataFrame(
        Target_Return=Float64[], MV_Return=Float64[], MV_CVaR=Float64[],
        Nom_Return=Float64[], Nom_CVaR=Float64[], Rob_Return=Float64[], Rob_CVaR=Float64[]
    )
    
    p_uniform = fill(1.0/size(X_all, 1), size(X_all, 1))
    
    for (tr_idx, tr) in enumerate(target_grid)
        # 1. MinVar
        w_m = solve_min_variance(cov_full, mu_full, tr, max_weight)
        ret_m = dot(mu_full, w_m)
        cvar_m = empirical_cvar(w_m, X_all, p_uniform, tau) * 100.0 # daily CVaR %
        
        # 2. Nominal CVaR
        w_n, cvar_n_obj = solve_nominal_cvar(X_all, mu_full ./ 252.0, tau, tr / 252.0, max_weight)
        ret_n = dot(mu_full, w_n)
        cvar_n = cvar_n_obj * 100.0 # daily CVaR %
        
        # 3. Robust SIP
        w_r, lb_r, ub_r, _, _ = solve_robust_sip(X_all, Y_all, grid_thetas_f, H_f, mu_full ./ 252.0, tau, tr / 252.0; max_iter=15, max_weight=max_weight)
        ret_r = dot(mu_full, w_r)
        cvar_r = ub_r * 100.0 # daily worst-case CVaR %
        
        push!(frontier_df, (tr, ret_m, cvar_m, ret_n, cvar_n, ret_r, cvar_r))
    end
    CSV.write(joinpath(output_dir, "frontier_data.csv"), frontier_df)
    println("Saved frontier_data.csv")
    
    # -------------------------------------------------------------------------
    # 7. GRID BENCHMARK VALIDATION & LIPSCHITZ CERTIFICATE
    # -------------------------------------------------------------------------
    println("Computing grid resolution benchmark and dispersion certificate...")
    # Representative window (Window 100)
    X_sub = X_all[100*21 : 100*21 + 1260 - 1, :]
    Y_sub = Y_all[100*21 : 100*21 + 1260 - 1, :]
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
    w_ad, lb_ad, ub_ad, act_ad, hist_ad = solve_robust_sip(X_sub, Y_sub, grid21, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0; max_iter=15, max_weight=max_weight)
    t_ad = time() - t0_ad
    
    # Dense LP on 21x21 (441 states)
    t0_d21 = time()
    w_d21, val_d21 = solve_master_cvar(X_sub, Y_sub, grid21, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0, max_weight)
    t_d21 = time() - t0_d21
    l1_ad_d21 = sum(abs.(w_ad - w_d21))
    
    # Dense LP on 41x41 (1681 states)
    vg41 = range(v_bnds[1], v_bnds[2], length=41)
    dg41 = range(d_bnds[1], d_bnds[2], length=41)
    grid41 = [[v, d] for v in vg41 for d in dg41]
    t0_d41 = time()
    w_d41, val_d41 = solve_master_cvar(X_sub, Y_sub, grid41, H_sub, mu_sub ./ 252.0, tau, t_ret_sub / 252.0, max_weight)
    t_d41 = time() - t0_d41
    l1_ad_d41 = sum(abs.(w_ad - w_d41))
    
    # Compute dispersion certificate for 21x21 and 41x41
    rho_21, L_Phi_21, cert_21 = compute_dispersion_certificate(v_bnds, d_bnds, 21, 21, H_sub, X_sub, tau)
    rho_41, L_Phi_41, cert_41 = compute_dispersion_certificate(v_bnds, d_bnds, 41, 41, H_sub, X_sub, tau)
    
    grid_bench_df = DataFrame(
        Method=["Adaptive SIP (21x21 oracle)", "Dense Grid (21x21, 441 states)", "Dense Grid (41x41, 1681 states)"],
        Active_States=[length(act_ad), 441, 1681],
        Runtime_sec=[t_ad, t_d21, t_d41],
        L1_Distance_to_Dense41=[l1_ad_d41, sum(abs.(w_d21 - w_d41)), 0.0],
        Dispersion_Radius_rho=[rho_21, rho_21, rho_41],
        Lipschitz_Certificate_Lrho=[cert_21, cert_21, cert_41]
    )
    CSV.write(joinpath(output_dir, "grid_comparison.csv"), grid_bench_df)
    
    # Export summary text
    open(joinpath(output_dir, "grid_validation.txt"), "w") do f
        write(f, "=== Robust SIP Computational and Empirical Validation Summary ===\n\n")
        write(f, "Total Rolling Windows: $(step_count)\n")
        write(f, "Average Active State Constraints in Master LP: $(round(mean(active_states_history), digits=2))\n")
        write(f, "Max Active State Constraints: $(maximum(active_states_history))\n")
        write(f, "Min Active State Constraints: $(minimum(active_states_history))\n")
        write(f, "ESS Distribution across Active States:\n")
        write(f, "  Min ESS: $(round(minimum(ess_history), digits=2))\n")
        write(f, "  5th Percentile ESS: $(round(percentile(ess_history, 5), digits=2))\n")
        write(f, "  Median ESS: $(round(median(ess_history), digits=2))\n")
        write(f, "  Mean ESS: $(round(mean(ess_history), digits=2))\n")
        write(f, "  Max ESS: $(round(maximum(ess_history), digits=2))\n")
        write(f, "  Average Tail Effective Sample Size (tau * ESS): $(round(mean(ess_history) * tau, digits=2))\n\n")
        write(f, "Representative Window Benchmark:\n")
        write(f, "  Adaptive SIP solve time: $(round(t_ad, digits=4)) s (Active States: $(length(act_ad)))\n")
        write(f, "  Dense Grid 21x21 solve time: $(round(t_d21, digits=4)) s, L1 dist to Adaptive: $(round(l1_ad_d21, digits=6))\n")
        write(f, "  Dense Grid 41x41 solve time: $(round(t_d41, digits=4)) s, L1 dist to Adaptive: $(round(l1_ad_d41, digits=6))\n")
        write(f, "  Spatial Dispersion Radius rho (21x21): $(round(rho_21, digits=4))\n")
        write(f, "  Lipschitz Inexact Oracle Certificate L_Phi * rho (21x21): $(round(cert_21, digits=4))\n")
    end
    println("Saved grid_validation.txt and grid_comparison.csv")
    println("All Julia pipeline tasks executed successfully.")
    
    rob_perf = results_df[results_df.Strategy .== "RobustSIP", :][1, :]
    return (
        Ann_Ret = rob_perf.Ann_Mean * 100.0,
        Volatility = rob_perf.Ann_Vol * 100.0,
        Sharpe = rob_perf.Sharpe,
        Max_DD = rob_perf.Max_DD * 100.0,
        Wealth = rob_perf.Final_Wealth,
        Turnover = rob_perf.Avg_Turnover * 100.0,
        Avg_ESS = mean(ess_history),
        Min_ESS = minimum(ess_history),
        Retained_Frac = mean(retained_frac_history) * 100.0
    )
end

if abspath(PROGRAM_FILE) == @__FILE__
    println("Executing comprehensive institutional pipeline...")
    run_institutional_backtest(0.0010, 0.05)
end
