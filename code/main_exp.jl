using Pkg
Pkg.activate(".")

using CSV, DataFrames, Dates, Statistics, LinearAlgebra
using Plots, JSON

include("RobustSIP.jl")
using .RobustSIP

function main()
    # Configuration
    data_path = "../data/aligned_market_data.csv"
    output_dir = "../figures"
    mkpath(output_dir)

    # Read Data
    println("Loading data...")
    df = CSV.read(data_path, DataFrame)
    returns_cols = names(df)[2:end-4] # Exclude Date, VIX, MarketReturn, Drawdown, logVIX
    X_all = Matrix{Float64}(df[:, returns_cols])
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])

    T_total, N = size(X_all)
    println("Total dataset size: $T_total days, $N assets")

    # Rolling Window Params
    window_size = 1260 # 5 years
    step_size = 21     # 1 month

    # Create Grid for Oracle
    vix_min, vix_max = minimum(Y_all[:, 1]), maximum(Y_all[:, 1])
    dd_min, dd_max = minimum(Y_all[:, 2]), maximum(Y_all[:, 2])
    vix_grid = range(vix_min, vix_max, length=21)
    dd_grid = range(dd_min, dd_max, length=21)
    grid_thetas = [ [v, d] for v in vix_grid for d in dd_grid ]

    # Arrays for storing results
    dates_out = Date[]
    wealth_eq = [1.0]
    wealth_mv = [1.0]
    wealth_nom = [1.0]
    wealth_rob = [1.0]

    w_eq_prev = fill(1.0/N, N)
    w_mv_prev = fill(1.0/N, N)
    w_nom_prev = fill(1.0/N, N)
    w_rob_prev = fill(1.0/N, N)

    trans_cost = 0.0010 # 10 bps

    tau = 0.05
    max_weight = 0.15

    # Arrays for new metrics
    all_weights_rob = []
    all_weights_mv = []
    all_weights_nom = []
    
    turnover_eq = []
    turnover_mv = []
    turnover_nom = []
    turnover_rob = []
    
    active_states_history = []
    master_lb_history = []
    oracle_ub_history = []

    println("Starting rolling backtest...")
    for t_start in 1:step_size:(T_total - window_size - step_size)
        t_end = t_start + window_size - 1
        t_hold_end = t_end + step_size
        
        # Training Data
        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        
        # Expected returns and cov (annualized approx for targets)
        mu_train = mean(X_train, dims=1)[:] * 252.0
        cov_train = cov(X_train) * 252.0
        
        # Bandwidth selection (Silverman's rule of thumb approx for 2D)
        sigma_vix = std(Y_train[:, 1])
        sigma_dd = std(Y_train[:, 2])
        n_train = size(Y_train, 1)
        h_vix = 1.06 * sigma_vix * n_train^(-1/6)
        h_dd = 1.06 * sigma_dd * n_train^(-1/6)
        H = [h_vix^2 0.0; 0.0 h_dd^2]
        
        # Target return = equal weight return
        target_return = mean(mu_train)
        
        # 1. Equal Weight
        w_eq = fill(1.0/N, N)
        
        # 2. Min Variance
        w_mv = solve_min_variance(cov_train, mu_train, target_return, max_weight)
        
        # 3. Nominal CVaR
        w_nom, _ = solve_nominal_cvar(X_train, mu_train ./ 252.0, tau, target_return / 252.0, max_weight)
        
        # 4. Robust SIP
        w_rob, lb, ub, active_thetas = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=10, max_weight=max_weight)
        
        push!(all_weights_rob, w_rob)
        push!(all_weights_mv, w_mv)
        push!(all_weights_nom, w_nom)
        push!(active_states_history, length(active_thetas))
        push!(master_lb_history, lb)
        push!(oracle_ub_history, ub)
        push!(dates_out, df.Date[t_end])
        
        # Out of Sample Evaluation
        X_test = X_all[t_end+1:t_hold_end, :]
        
        ret_eq = sum(X_test * w_eq)
        ret_mv = sum(X_test * w_mv)
        ret_nom = sum(X_test * w_nom)
        ret_rob = sum(X_test * w_rob)
        
        # Turnover
        to_eq = sum(abs.(w_eq - w_eq_prev))
        to_mv = sum(abs.(w_mv - w_mv_prev))
        to_nom = sum(abs.(w_nom - w_nom_prev))
        to_rob = sum(abs.(w_rob - w_rob_prev))
        
        push!(turnover_eq, to_eq)
        push!(turnover_mv, to_mv)
        push!(turnover_nom, to_nom)
        push!(turnover_rob, to_rob)
        
        push!(wealth_eq, wealth_eq[end] * (1.0 + ret_eq - to_eq * trans_cost))
        push!(wealth_mv, wealth_mv[end] * (1.0 + ret_mv - to_mv * trans_cost))
        push!(wealth_nom, wealth_nom[end] * (1.0 + ret_nom - to_nom * trans_cost))
        push!(wealth_rob, wealth_rob[end] * (1.0 + ret_rob - to_rob * trans_cost))
        
        w_eq_prev = w_eq
        w_mv_prev = w_mv
        w_nom_prev = w_nom
        w_rob_prev = w_rob
        
        println("Date: $(df.Date[t_end]) | W_rob: $(round(wealth_rob[end], digits=2)) | Active States: $(length(active_thetas))")
    end

    println("Backtest Complete. Generating figures...")

    dates_plot = [df.Date[window_size]; dates_out]
    dates_hist = dates_out

    # Figure 4: Wealth paths
    p_wealth = plot(dates_plot, wealth_eq, label="1/N", linewidth=2)
    plot!(p_wealth, dates_plot, wealth_mv, label="MinVar", linewidth=2)
    plot!(p_wealth, dates_plot, wealth_nom, label="Nominal CVaR", linewidth=2)
    plot!(p_wealth, dates_plot, wealth_rob, label="Robust SIP", linewidth=2, color=:red)
    title!(p_wealth, "Out-of-Sample Wealth (10 bps TC)")
    savefig(p_wealth, joinpath(output_dir, "wealth_plot.pdf"))

    # Calculate drawdowns
    dd_eq = wealth_eq ./ [maximum(wealth_eq[1:i]) for i in 1:length(wealth_eq)] .- 1.0
    dd_mv = wealth_mv ./ [maximum(wealth_mv[1:i]) for i in 1:length(wealth_mv)] .- 1.0
    dd_nom = wealth_nom ./ [maximum(wealth_nom[1:i]) for i in 1:length(wealth_nom)] .- 1.0
    dd_rob = wealth_rob ./ [maximum(wealth_rob[1:i]) for i in 1:length(wealth_rob)] .- 1.0

    # Figure 5: Drawdown paths
    p_dd = plot(dates_plot, dd_eq, label="1/N")
    plot!(p_dd, dates_plot, dd_mv, label="MinVar")
    plot!(p_dd, dates_plot, dd_nom, label="Nominal CVaR")
    plot!(p_dd, dates_plot, dd_rob, label="Robust SIP", color=:red)
    title!(p_dd, "Out-of-Sample Drawdowns")
    savefig(p_dd, joinpath(output_dir, "drawdown_plot.pdf"))

    # Convert weights to Matrix
    mat_w_rob = reduce(hcat, all_weights_rob)'
    mat_w_mv = reduce(hcat, all_weights_mv)'
    
    # Figure 6: Robust SIP Weights
    p_w_rob = areaplot(dates_hist, mat_w_rob, title="Robust SIP Allocations", legend=false, linewidth=0)
    savefig(p_w_rob, joinpath(output_dir, "weights_rob_plot.pdf"))
    
    # Figure 7: MinVar Weights
    p_w_mv = areaplot(dates_hist, mat_w_mv, title="MinVar Allocations", legend=false, linewidth=0)
    savefig(p_w_mv, joinpath(output_dir, "weights_mv_plot.pdf"))

    # Figure 8: Monthly Turnover
    p_to = plot(dates_hist, turnover_eq, label="1/N")
    plot!(p_to, dates_hist, turnover_mv, label="MinVar")
    plot!(p_to, dates_hist, turnover_nom, label="Nominal CVaR")
    plot!(p_to, dates_hist, turnover_rob, label="Robust SIP", color=:red)
    title!(p_to, "Monthly Portfolio Turnover")
    savefig(p_to, joinpath(output_dir, "turnover_plot.pdf"))
    
    # Figure 9: Active states over time
    p_states = bar(dates_hist, active_states_history, legend=false, title="Number of Active Stress States Selected")
    savefig(p_states, joinpath(output_dir, "active_states_plot.pdf"))
    
    # Figure 10: Master-Oracle Convergence Bounds (for the last iteration as an example)
    p_bounds = plot(dates_hist, master_lb_history, label="Master LB")
    plot!(p_bounds, dates_hist, oracle_ub_history, label="Oracle UB")
    title!(p_bounds, "Master-Oracle Bounds Gap")
    savefig(p_bounds, joinpath(output_dir, "bounds_plot.pdf"))

    # Figure 11: In-sample Efficient Frontier (approximation using last train window)
    ret_grid = range(0.0, maximum(mean(X_all, dims=1))*252.0, length=20)
    cvar_front = Float64[]
    for r in ret_grid
        w_f, _ = solve_nominal_cvar(X_all[end-window_size+1:end, :], mean(X_all[end-window_size+1:end, :], dims=1)[:] * 252.0, tau, r / 252.0, max_weight)
        push!(cvar_front, empirical_cvar(w_f, X_all[end-window_size+1:end, :], fill(1.0/window_size, window_size), tau))
    end
    p_front = plot(cvar_front, ret_grid, label="Nominal Frontier", xlabel="CVaR", ylabel="Expected Return")
    title!(p_front, "In-sample Efficient Frontier")
    savefig(p_front, joinpath(output_dir, "frontier_plot.pdf"))
    
    # Figure 12: Kernel density map of crisis states (Scatter of VIX vs DD colored by density approx)
    p_kernel = scatter(Y_all[:, 1], Y_all[:, 2], alpha=0.3, xlabel="log(VIX)", ylabel="Drawdown", legend=false, title="Market States Support")
    savefig(p_kernel, joinpath(output_dir, "kernel_map_plot.pdf"))

    # Figure 13: Bootstrap distribution of Sharpe difference
    recs = length(wealth_rob)
    diff_sharpe = Float64[]
    block_size = 12
    for b in 1:1000
        idx = rand(1:(recs-block_size), div(recs, block_size))
        samp_rob = vcat([wealth_rob[i:i+block_size-1] for i in idx]...)
        samp_nom = vcat([wealth_nom[i:i+block_size-1] for i in idx]...)
        ret_s_rob = diff(samp_rob) ./ samp_rob[1:end-1]
        ret_s_nom = diff(samp_nom) ./ samp_nom[1:end-1]
        push!(diff_sharpe, (mean(ret_s_rob)/std(ret_s_rob)) - (mean(ret_s_nom)/std(ret_s_nom)))
    end
    p_boot = histogram(diff_sharpe, bins=50, legend=false, title="Bootstrap Distribution: Sharpe Difference (Rob - Nom)")
    savefig(p_boot, joinpath(output_dir, "bootstrap_plot.pdf"))

    # Save results
    results = Dict(
        "wealth_eq" => wealth_eq[end],
        "wealth_mv" => wealth_mv[end],
        "wealth_nom" => wealth_nom[end],
        "wealth_rob" => wealth_rob[end]
    )
    open("../code/results.json", "w") do f
        JSON.print(f, results, 4)
    end

    println("Done.")
end

main()
