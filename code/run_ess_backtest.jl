using CSV, DataFrames, Statistics, LinearAlgebra, Base.Threads

include("RobustSIP.jl")
using .RobustSIP

function run_ess_backtests()
    println("Starting ESS full backtests...")
    data_path = "../data/aligned_market_data.csv"
    output_dir = "../results"
    
    df = CSV.read(data_path, DataFrame)
    X_raw = Matrix(df[:, 2:31])
    Y_raw = Matrix(df[:, 32:33])
    
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]
    
    T_total, N = size(X_all)
    window_size = 1260
    step_size = 21
    max_weight = 0.15
    tau = 0.05
    
    ess_thresholds = [0.0, 10.0, 20.0, 40.0]
    
    # Run in parallel
    results = Vector{Any}(undef, length(ess_thresholds))
    
    Threads.@threads for i in 1:length(ess_thresholds)
        E_min = ess_thresholds[i]
        println("Running backtest for ESS_Min = ", E_min)
        rets = Float64[]
        turnover = Float64[]
        w_prev = fill(1.0/N, N)
        
        ess_history = Float64[]
        min_ess_history = Float64[]
        retained_frac_history = Float64[]
        
        step_indices = 1:step_size:(T_total - window_size - step_size + 1)
        total_steps = length(step_indices)
        
        for (step_count, t_start) in enumerate(step_indices)
            t_end = t_start + window_size - 1
            X_train = X_all[t_start:t_end, :]
            Y_train = Y_all[t_start:t_end, :]
            mu_train = mean(X_train, dims=1)[:] * 252.0
            target_return = median(mu_train) / 252.0
            
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
            
            grid_thetas = Vector{Float64}[]
            for th in raw_thetas
                w_th = get_kernel_weights(Y_train, th, H)
                ess = 1.0 / sum(w_th.^2)
                if ess >= E_min
                    push!(grid_thetas, th)
                end
            end
            
            retained_frac = length(grid_thetas) / length(raw_thetas)
            push!(retained_frac_history, retained_frac)
            
            if isempty(grid_thetas)
                w_rob = fill(1.0/N, N)
                active_thetas = []
            else
                w_rob, _, _, active_thetas, _ = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, target_return; max_iter=15, tol=1e-4, max_weight=max_weight)
            end
            
            active_ess_vals = [effective_sample_size(get_kernel_weights(Y_train, th, H)) for th in active_thetas]
            avg_ess = isempty(active_ess_vals) ? 0.0 : mean(active_ess_vals)
            min_ess = isempty(active_ess_vals) ? 0.0 : minimum(active_ess_vals)
            push!(ess_history, avg_ess)
            push!(min_ess_history, min_ess)
            
            X_hold = X_all[t_end+1:t_end+step_size, :]
            for t_h in 1:step_size
                r_t = X_hold[t_h, :]
                port_ret = sum(w_rob .* r_t)
                push!(rets, port_ret)
            end
            
            if step_count > 1
                w_drift = w_prev .* (1.0 .+ X_hold[1, :])
                w_drift ./= sum(w_drift)
                push!(turnover, sum(abs.(w_rob - w_drift)))
            end
            w_prev = copy(w_rob)
        end
        
        # Calculate performance
        ann_ret = mean(rets) * 252.0
        ann_vol = std(rets) * sqrt(252.0)
        sharpe = ann_ret / ann_vol
        
        cum_ret = cumprod(1.0 .+ rets)
        running_max = accumulate(max, cum_ret)
        drawdowns = (cum_ret .- running_max) ./ running_max
        max_dd = minimum(drawdowns)
        
        avg_turn = isempty(turnover) ? 0.0 : mean(turnover)
        
        results[i] = (
            E_min, ann_ret, ann_vol, sharpe, max_dd, cum_ret[end], avg_turn,
            mean(ess_history), minimum(min_ess_history), mean(retained_frac_history)
        )
        println("Finished ESS_Min = ", E_min)
    end
    
    ess_res_df = DataFrame(
        ESS_Min=Float64[], Ann_Return_Decimal=Float64[], Ann_Vol_Decimal=Float64[], 
        Sharpe=Float64[], Max_DD_Decimal=Float64[], Wealth=Float64[], Turnover_Decimal=Float64[],
        Avg_ESS=Float64[], Min_ESS=Float64[], Retained_Frac_Decimal=Float64[]
    )
    
    for i in 1:length(ess_thresholds)
        push!(ess_res_df, results[i])
    end
    
    CSV.write(joinpath(output_dir, "ess_full_backtest.csv"), ess_res_df)
    println("Done!")
end

run_ess_backtests()
