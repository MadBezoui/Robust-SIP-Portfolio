using Pkg
Pkg.activate(".")

using CSV, DataFrames, Dates, Statistics, LinearAlgebra, StatsBase, Random, Printf
include("RobustSIP.jl")
using .RobustSIP

function run_all_sensitivities()
    println("Starting Sensitivity Analyses...")
    data_path = "../data/aligned_market_data.csv"
    output_dir = "../figures"
    mkpath(output_dir)

    df = CSV.read(data_path, DataFrame)
    col_names = names(df)
    vix_idx = findfirst(x -> x == "VIX", col_names)
    returns_cols = col_names[2:(vix_idx - 1)]
    
    X_raw = Matrix{Float64}(df[:, returns_cols])
    Y_raw = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])
    
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]

    T_total, N = size(X_all)
    window_size = 1260
    step_size = 21
    max_weight = 0.15
    tau = 0.05

    step_indices = 1:step_size:(T_total - window_size - step_size + 1)
    subset_indices = step_indices[1:18:end]
    if length(subset_indices) > 20
        subset_indices = subset_indices[1:20]
    end

    grid_sizes = [11, 21, 41, 81]
    grid_res_df = DataFrame(Grid_Size=Int[], Avg_Runtime=Float64[], Avg_Active_States=Float64[], Avg_Worst_CVaR=Float64[])
    
    c_vals = [0.5, 0.75, 1.0, 1.5, 2.0]
    bw_res_df = DataFrame(Multiplier=Float64[], Avg_Active_States=Float64[], Avg_Worst_CVaR=Float64[])
    
    for g in grid_sizes
        rt_sum = 0.0
        act_sum = 0.0
        cvar_sum = 0.0
        for t_start in subset_indices
            t_end = t_start + window_size - 1
            X_train = X_all[t_start:t_end, :]
            Y_train = Y_all[t_start:t_end, :]
            mu_train = mean(X_train, dims=1)[:] * 252.0
            
            sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
            n_train = size(Y_train, 1)
            H = [(sigma_vix * n_train^(-1/6))^2 0.0; 0.0 (sigma_dd * n_train^(-1/6))^2]
            
            vix_min, vix_max = extrema(Y_train[:, 1])
            dd_min, dd_max = extrema(Y_train[:, 2])
            delta_v = 0.10 * (vix_max - vix_min)
            delta_d = 0.10 * (dd_max - dd_min)
            
            vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=g)
            dd_grid  = range(max(0.0, dd_min - delta_d), min(1.0, dd_max + delta_d), length=g)
            grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]
            
            t0 = time()
            w_rob, lb, ub, active_thetas, _ = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, median(mu_train) / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
            rt_sum += (time() - t0)
            act_sum += length(active_thetas)
            cvar_sum += ub
        end
        n_sub = length(subset_indices)
        push!(grid_res_df, (g, rt_sum / n_sub, act_sum / n_sub, (cvar_sum / n_sub) * 100.0))
        println("Finished grid size $g")
    end
    CSV.write(joinpath(output_dir, "grid_sensitivity.csv"), grid_res_df)

    for c in c_vals
        act_sum = 0.0
        cvar_sum = 0.0
        for t_start in subset_indices
            t_end = t_start + window_size - 1
            X_train = X_all[t_start:t_end, :]
            Y_train = Y_all[t_start:t_end, :]
            mu_train = mean(X_train, dims=1)[:] * 252.0
            
            sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
            n_train = size(Y_train, 1)
            H = [(c * sigma_vix * n_train^(-1/6))^2 0.0; 0.0 (c * sigma_dd * n_train^(-1/6))^2]
            
            vix_min, vix_max = extrema(Y_train[:, 1])
            dd_min, dd_max = extrema(Y_train[:, 2])
            delta_v = 0.10 * (vix_max - vix_min)
            delta_d = 0.10 * (dd_max - dd_min)
            
            vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=21)
            dd_grid  = range(max(0.0, dd_min - delta_d), min(1.0, dd_max + delta_d), length=21)
            grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]
            
            w_rob, lb, ub, active_thetas, _ = solve_robust_sip(X_train, Y_train, grid_thetas, H, mu_train ./ 252.0, tau, median(mu_train) / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
            act_sum += length(active_thetas)
            cvar_sum += ub
        end
        n_sub = length(subset_indices)
        push!(bw_res_df, (c, act_sum / n_sub, (cvar_sum / n_sub) * 100.0))
        println("Finished bw multiplier $c")
    end
    CSV.write(joinpath(output_dir, "bandwidth_sensitivity.csv"), bw_res_df)

    ts_path = joinpath(output_dir, "strategy_monthly_returns.csv")
    if isfile(ts_path)
        ts_df = CSV.read(ts_path, DataFrame)
        rets_rob = ts_df.RobustSIP_Ret
        rets_nom = ts_df.NominalCVaR_Ret
        
        block_lengths = [6, 9, 12, 18, 24]
        boot_res_df = DataFrame(Block_Length=Int[], P_Value=Float64[], SE=Float64[])
        
        function quick_boot(r1, r2, b_len)
            Random.seed!(2026)
            T = length(r1)
            sr1 = (mean(r1) / std(r1)) * sqrt(12.0)
            sr2 = (mean(r2) / std(r2)) * sqrt(12.0)
            diff_orig = sr1 - sr2
            
            boot_diffs = Float64[]
            for b in 1:5000
                start_indices = rand(1:T, div(T, b_len) + 1)
                boot_idx = Int[]
                for s in start_indices
                    append!(boot_idx, [mod1(s + i - 1, T) for i in 1:b_len])
                end
                boot_idx = boot_idx[1:T]
                
                s1 = r1[boot_idx]
                s2 = r2[boot_idx]
                push!(boot_diffs, sqrt(12.0) * ((mean(s1)/std(s1)) - (mean(s2)/std(s2))))
            end
            p_val = mean(abs.(boot_diffs .- mean(boot_diffs)) .>= abs(diff_orig))
            return p_val, std(boot_diffs)
        end
        
        for b in block_lengths
            p_val, se = quick_boot(rets_rob, rets_nom, b)
            push!(boot_res_df, (b, p_val, se))
        end
        CSV.write(joinpath(output_dir, "block_length_sensitivity.csv"), boot_res_df)
    end
    
    ess_thresholds = [0.0, 10.0, 20.0, 40.0, 60.0, 100.0]
    ess_res_df = DataFrame(ESS_Min=Float64[], Avg_Retained_States=Float64[], Avg_Worst_CVaR=Float64[])
    
    for E_min in ess_thresholds
        ret_states_sum = 0.0
        cvar_sum = 0.0
        for t_start in subset_indices
            t_end = t_start + window_size - 1
            X_train = X_all[t_start:t_end, :]
            Y_train = Y_all[t_start:t_end, :]
            mu_train = mean(X_train, dims=1)[:] * 252.0
            
            sigma_vix, sigma_dd = std(Y_train[:, 1]), std(Y_train[:, 2])
            n_train = size(Y_train, 1)
            H = [(sigma_vix * n_train^(-1/6))^2 0.0; 0.0 (sigma_dd * n_train^(-1/6))^2]
            
            vix_min, vix_max = extrema(Y_train[:, 1])
            dd_min, dd_max = extrema(Y_train[:, 2])
            delta_v = 0.10 * (vix_max - vix_min)
            delta_d = 0.10 * (dd_max - dd_min)
            
            vix_grid = range(vix_min - delta_v, vix_max + delta_v, length=21)
            dd_grid  = range(max(0.0, dd_min - delta_d), min(1.0, dd_max + delta_d), length=21)
            
            valid_thetas = Vector{Vector{Float64}}()
            for v in vix_grid
                for d in dd_grid
                    th = [v, d]
                    w = get_kernel_weights(Y_train, th, H)
                    ess = 1.0 / sum(w.^2)
                    if ess >= E_min
                        push!(valid_thetas, th)
                    end
                end
            end
            
            if isempty(valid_thetas)
                push!(valid_thetas, [mean(Y_train[:, 1]), mean(Y_train[:, 2])])
            end
            
            w_rob, lb, ub, active_thetas, _ = solve_robust_sip(X_train, Y_train, valid_thetas, H, mu_train ./ 252.0, tau, median(mu_train) / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
            ret_states_sum += length(valid_thetas)
            cvar_sum += ub
        end
        n_sub = length(subset_indices)
        push!(ess_res_df, (E_min, ret_states_sum / n_sub, (cvar_sum / n_sub) * 100.0))
        println("Finished ESS threshold $E_min")
    end
    CSV.write(joinpath(output_dir, "ess_sensitivity.csv"), ess_res_df)
    println("All Sensitivity Analyses Completed!")
end

run_all_sensitivities()
