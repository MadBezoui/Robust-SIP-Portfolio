using CSV, DataFrames, Statistics, LinearAlgebra

include("RobustSIP.jl")
using .RobustSIP

function run_ess_backtests()
    println("Starting ESS full backtests...")
    data_path = joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")
    output_dir = joinpath(@__DIR__, "..", "results")
    out_file = joinpath(output_dir, "ess_full_backtest.csv")
    
    df = CSV.read(data_path, DataFrame)
    X_raw = Matrix(df[:, 2:31])
    Y_raw = Matrix(df[:, ["logVIX", "Drawdown"]])
    
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]
    
    T_total, N = size(X_all)
    window_size = 1260
    step_size = 21
    max_weight = 0.15
    tau = 0.05
    trans_cost = 0.0010
    
    ess_thresholds = [0.0, 10.0, 20.0, 40.0]
    
    # Load existing results to avoid recomputation
    existing_thresholds = Float64[]
    if isfile(out_file)
        existing_df = CSV.read(out_file, DataFrame)
        existing_thresholds = existing_df.ESS_Min
        println("Found existing results for thresholds: ", existing_thresholds)
    else
        existing_df = DataFrame(
            ESS_Min=Float64[], Ann_Return_Decimal=Float64[], Ann_Vol_Decimal=Float64[],
            Sharpe=Float64[], Max_DD_Decimal=Float64[], Wealth=Float64[], Turnover_Decimal=Float64[],
            Avg_ESS=Float64[], Min_ESS=Float64[], Retained_Frac_Decimal=Float64[]
        )
    end
    
    for E_min in ess_thresholds
        if E_min in existing_thresholds
            println("Skipping ESS_Min = $E_min (already computed)")
            continue
        end
        
        println("Computing ESS_Min = $E_min ...")
        rets = Float64[]
        turnover = Float64[]
        w_prev = fill(1.0/N, N)
        
        ess_history = Float64[]
        min_ess_history = Float64[]
        retained_frac_history = Float64[]
        
        step_indices = 1:step_size:(T_total - window_size - step_size + 1)
        step_count = 0
        
        for t_start in step_indices
            step_count += 1
            t_end = t_start + window_size - 1
            
            X_train = X_all[t_start:t_end, :]
            Y_train = Y_all[t_start:t_end, :]
            mu_train = vec(mean(X_train, dims=1)) .* 252.0
            target_return = median(mu_train)
            
            sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
            n_train = size(Y_train, 1)
            H = [(sigma_vix * n_train^(-1/6))^2 0.0; 0.0 (sigma_dd * n_train^(-1/6))^2]
            
            vix_min, vix_max = extrema(Y_train[:, 1])
            dd_min, dd_max = extrema(Y_train[:, 2])
            delta_v = 0.10 * (vix_max - vix_min)
            delta_d = 0.10 * (dd_max - dd_min)
            
            vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=21)
            dd_grid  = range(max(0.0, dd_min - delta_d), min(1.0, dd_max + delta_d), length=21)
            raw_thetas = [[v, d] for v in vix_grid for d in dd_grid]
            
            grid_thetas = Vector{Vector{Float64}}()
            for th in raw_thetas
                w_th = get_kernel_weights(Y_train, th, H)
                ess = 1.0 / sum(w_th.^2)
                if ess >= E_min
                    push!(grid_thetas, th)
                end
            end
            
            push!(retained_frac_history, length(grid_thetas) / length(raw_thetas))
            
            if isempty(grid_thetas)
                w_rob = fill(1.0/N, N)
                active_thetas = []
            else
                w_rob, _, _, active_thetas, _, _, _, _, _ = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
            end
            
            active_ess_vals = [1.0 / sum(get_kernel_weights(Y_train, th, H).^2) for th in active_thetas]
            push!(ess_history, isempty(active_ess_vals) ? 0.0 : mean(active_ess_vals))
            push!(min_ess_history, isempty(active_ess_vals) ? 0.0 : minimum(active_ess_vals))
            
            X_hold = X_all[t_end+1:t_end+step_size, :]
            
            w_prev_adj = copy(w_prev)
            if step_count > 1
                ret_prev_hold = vec(prod(1.0 .+ X_all[t_start - step_size : t_start - 1, :], dims=1)) .- 1.0
                w_prev_adj = w_prev .* (1.0 .+ ret_prev_hold)
                w_prev_adj ./= sum(w_prev_adj)
            end
            turn = sum(abs.(w_rob - w_prev_adj)) / 2.0
            push!(turnover, turn)
            
            ret_rob_h = sum(w_rob .* vec(prod(1.0 .+ X_hold, dims=1) .- 1.0))
            push!(rets, ret_rob_h - trans_cost * turn)
            
            w_prev = copy(w_rob)
        end
        
        periods_per_year = 252.0 / step_size
        ann_ret = mean(rets) * periods_per_year
        ann_vol = std(rets) * sqrt(periods_per_year)
        sharpe = ann_ret / ann_vol
        cum_ret = cumprod(1.0 .+ rets)
        drawdowns = (cum_ret .- accumulate(max, cum_ret)) ./ accumulate(max, cum_ret)
        max_dd = minimum(drawdowns)
        
        push!(existing_df, (
            E_min, ann_ret, ann_vol, sharpe, max_dd, cum_ret[end], mean(turnover),
            mean(ess_history), minimum(min_ess_history), mean(retained_frac_history)
        ))
        
        # Save intermediate result immediately
        CSV.write(out_file, existing_df)
        println("Finished and saved ESS_Min = ", E_min)
    end
    println("Done!")
end

if abspath(PROGRAM_FILE) == @__FILE__
    run_ess_backtests()
end
