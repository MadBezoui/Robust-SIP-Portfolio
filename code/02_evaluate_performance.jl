using Statistics, Random

function lw_studentized_bootstrap(rets1::Vector{Float64}, rets2::Vector{Float64}, block_size::Int=12, n_reps::Int=5000; seed::Int=20260821)
    Random.seed!(seed)
    T = length(rets1)
    
    # Original Sharpe ratios
    sr1_ann = (mean(rets1) / std(rets1)) * sqrt(12.0)
    sr2_ann = (mean(rets2) / std(rets2)) * sqrt(12.0)
    diff_orig = sr1_ann - sr2_ann
    
    boot_t_stats = Float64[]
    
    for b in 1:n_reps
        # Circular block bootstrap sampling
        start_indices = rand(1:T, div(T, block_size) + 1)
        boot_idx = Int[]
        for s in start_indices
            append!(boot_idx, [mod1(s + i - 1, T) for i in 1:block_size])
        end
        boot_idx = boot_idx[1:T]
        
        samp1 = rets1[boot_idx]
        samp2 = rets2[boot_idx]
        
        # Bootstrap Sharpe difference
        ds_boot = sqrt(12.0) * ((mean(samp1) / std(samp1)) - (mean(samp2) / std(samp2)))
        
        # For studentization, we approximate the standard error of the bootstrap sample
        # Since exact influence-function variance is complex to compute inside the bootstrap loop,
        # we use a standard proxy: the block-wise variance of the Sharpe difference.
        se_boot = std(samp1 - samp2) / sqrt(T) # Simplified SE for the difference
        
        # Studentized statistic (t-stat)
        t_stat = (ds_boot - diff_orig) / (se_boot + 1e-8)
        push!(boot_t_stats, t_stat)
    end
    
    # Original SE proxy
    se_orig = std(rets1 - rets2) / sqrt(T)
    
    # Compute p-value using the studentized distribution
    t_orig = diff_orig / se_orig
    p_val = (1.0 + sum(abs.(boot_t_stats) .>= abs(t_orig))) / (n_reps + 1.0)
    
    # Confidence intervals
    ci_lower = diff_orig - custom_percentile(boot_t_stats, 97.5) * se_orig
    ci_upper = diff_orig - custom_percentile(boot_t_stats, 2.5) * se_orig
    
    return diff_orig, se_orig, ci_lower, ci_upper, p_val
end

function custom_percentile(v, p)
    sv = sort(v)
    idx = max(1, min(length(v), round(Int, p / 100 * length(v))))
    return sv[idx]
end
using Pkg
Pkg.activate(".")

using CSV, DataFrames, Dates, Statistics, LinearAlgebra, StatsBase, Random, Printf

include("RobustSIP.jl")
using .RobustSIP

"""
Paired Circular Moving-Block Bootstrap for Annualized Sharpe Ratio Differences.
"""

"""
Calculate comprehensive 14 performance metrics.
"""
function calculate_metrics(returns::AbstractVector, weights_matrix::AbstractMatrix, turnover::AbstractVector, tc::Float64)
    valid_returns = collect(skipmissing(returns))
    T_out = length(valid_returns)
    if T_out == 0
        return (missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing)
    end
    ann_mean = mean(valid_returns) * 12.0
    ann_vol = std(valid_returns) * sqrt(12.0)
    sharpe = ann_vol > 0 ? (ann_mean / ann_vol) : 0.0
    
    # Downside deviation relative to MAR = 0
    downside_dev = sqrt(mean(min.(valid_returns, 0.0).^2)) * sqrt(12.0)
    sortino = downside_dev > 0 ? (ann_mean / downside_dev) : Inf
    
    # Wealth including initial wealth 1.0
    wealth = vcat(1.0, cumprod(1.0 .+ valid_returns))
    running_peak = accumulate(max, wealth)
    drawdowns = wealth ./ running_peak .- 1.0
    max_dd = minimum(drawdowns)
    
    # CAGR and Calmar Ratio
    cagr = wealth[end]^(12.0 / T_out) - 1.0
    calmar = abs(max_dd) > 0 ? (cagr / abs(max_dd)) : Inf
    
    # Realized Holding-Period Expected Shortfall (CVaR on holding-period losses)
    losses = -valid_returns
    sorted_losses = sort(losses, rev=true) # worst losses first
    function exact_cvar(losses, alpha)
        T_out = length(losses)
        k = floor(Int, alpha * T_out)
        f = alpha * T_out - k
        if k == 0
            return losses[1]
        elseif k == T_out
            return mean(losses)
        else
            return (sum(losses[1:k]) + f * losses[k+1]) / (alpha * T_out)
        end
    end
    cvar_95_holding = exact_cvar(sorted_losses, 0.05)
    cvar_99_holding = exact_cvar(sorted_losses, 0.01)
    
    valid_turnover = collect(skipmissing(turnover))
    avg_turnover = isempty(valid_turnover) ? 0.0 : mean(valid_turnover)
    tc_drag = avg_turnover * tc * 12.0 # Annualized in decimal
    
    # Concentration (Effective N)
    eff_n_vals = [1.0 / sum(weights_matrix[i, :].^2) for i in 1:size(weights_matrix, 1) if !any(ismissing.(weights_matrix[i, :]))]
    eff_n = isempty(eff_n_vals) ? missing : mean(eff_n_vals)
    worst_period = minimum(valid_returns)
    
    return (ann_mean, ann_vol, sharpe, sortino, cvar_95_holding, cvar_99_holding, max_dd, cagr, calmar, avg_turnover, tc_drag, eff_n, worst_period, wealth[end])
end


function evaluate_backtest(trans_cost::Float64=0.0010, tau::Float64=0.05)
    output_dir = "../results"
    calendar_df = CSV.read(joinpath(output_dir, "calendar.csv"), DataFrame)
    strat_names = ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
    
    rets_dict = Dict{String, Vector{Float64}}()
    rets_gross_dict = Dict{String, Vector{Float64}}()
    turnover_dict = Dict{String, Vector{Float64}}()
    weights_dict = Dict{String, Vector{Vector{Float64}}}()
    
    for s in strat_names
        s_safe = replace(s, "/" => "")
        df_w = CSV.read(joinpath(output_dir, "weights_$(s_safe).csv"), DataFrame)
        w_mat = Matrix(df_w[:, 1:end-1])
        weights_dict[s] = [w_mat[i, :] for i in 1:size(w_mat,1)]
        
        df_perf = CSV.read(joinpath(output_dir, "perf_$(s_safe).csv"), DataFrame)
        rets_dict[s] = df_perf.Return
        rets_gross_dict[s] = df_perf.Return_Gross
        turnover_dict[s] = df_perf.Turnover
    df = CSV.read("../data/aligned_market_data.csv", DataFrame)
    col_names = names(df)
    vix_idx = findfirst(x -> x == "VIX", col_names)
    returns_cols = col_names[2:(vix_idx - 1)]
    X_raw = Matrix{Float64}(df[:, returns_cols])
    Y_raw = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]
    max_weight = 0.15
    end

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
        diff, se, ci_l, ci_u, p_val, boot_dist = lw_studentized_bootstrap(
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
    
    active_hist_df = DataFrame(Window=1:step_count, Active_States=active_states_history, Iterations=iterations_history, Avg_Active_State_ESS=ess_history)
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
end

if abspath(PROGRAM_FILE) == @__FILE__
    evaluate_backtest(0.0010, 0.05)
end
