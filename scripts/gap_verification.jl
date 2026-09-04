using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf
include("RobustSIP.jl")
using .RobustSIP

function run_gap_verification()
    println("Running Gap Verification...")
    data_path = joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")
    output_dir = joinpath(@__DIR__, "..", "results")
    
    df = CSV.read(data_path, DataFrame)
    X_raw = Matrix(df[:, 2:31])
    Y_raw = Matrix(df[:, ["logVIX", "Drawdown"]])
    
    X_all = X_raw[2:end, :]
    Y_all = Y_raw[1:end-1, :]
    dates = df.Date[2:end]
    
    target_dates = [
        Date(1998, 8, 31),
        Date(2008, 10, 31),
        Date(2013, 5, 31),
        Date(2020, 3, 31),
        Date(2022, 9, 30)
    ]
    labels = ["1998-08 (LTCM)", "2008-10 (Lehman)", "2013-05 (Taper Tantrum)", "2020-03 (COVID-19)", "2022-09 (Inflation Shock)"]
    
    L = 1260
    tau = 0.05
    n_v, n_d = 21, 21
    max_weight = 0.15
    
    res_df = DataFrame(
        Label = String[],
        MaxGradNorm = Float64[],
        GridDisp = Float64[],
        EmpiricalProduct = Float64[],
        LocalSearchImp = Float64[]
    )
    
    for (i, d) in enumerate(target_dates)
        idx = findlast(x -> x <= d, dates)
        if isnothing(idx) || idx <= L
            println("Skipping $d")
            continue
        end
        
        start_idx = idx - L
        end_idx = idx - 1
        X_train = X_all[start_idx:end_idx, :]
        Y_train = Y_all[start_idx:end_idx, :]
        
        v_min, v_max = minimum(Y_train[:,1]), maximum(Y_train[:,1])
        d_min, d_max = minimum(Y_train[:,2]), maximum(Y_train[:,2])
        v_margin = 0.1 * (v_max - v_min)
        d_margin = 0.1 * (d_max - d_min)
        bounds_v = (v_min - v_margin, v_max + v_margin)
        bounds_d = (max(0.0, d_min - d_margin), min(1.0, d_max + d_margin))
        
        std_v = std(Y_train[:,1])
        std_d = std(Y_train[:,2])
        c = 1.0
        H = (size(Y_train, 1)^(-1/3)) * [ (c * std_v)^2 0.0 ; 0.0 (c * std_d)^2 ]
        
        mu_train = vec(mean(X_train, dims=1)) .* 252.0
        target_return = median(mu_train)
        
        v_grid = range(bounds_v[1], bounds_v[2], length=n_v)
        d_grid = range(bounds_d[1], bounds_d[2], length=n_d)
        grid_21 = [[v, d] for v in v_grid for d in d_grid]
        
        w_opt, _, val_21, active_thetas, _, _, _, _, _ = RobustSIP.solve_robust_sip(X_train, Y_train, grid_21, H, mu_train ./ 252.0, tau, target_return / 252.0; max_iter=15, tol=1e-4, max_weight=max_weight)
        
        v_grid_ref = range(bounds_v[1], bounds_v[2], length=201)
        d_grid_ref = range(bounds_d[1], bounds_d[2], length=201)
        grid_ref = [[v, d] for v in v_grid_ref for d in d_grid_ref]
        
        max_grad_norm = 0.0
        cvar_vals = zeros(length(grid_ref))
        for (j, th) in enumerate(grid_ref)
            g = RobustSIP.grad_cvar_theta(w_opt, th, X_train, Y_train, H, tau)
            max_grad_norm = max(max_grad_norm, norm(g))
            _, cv = RobustSIP.solve_oracle(w_opt, X_train, Y_train, [th], H, tau)
            cvar_vals[j] = cv
        end
        val_ref = maximum(cvar_vals)
        
        idx_top = sortperm(cvar_vals, rev=true)[1:5]
        top_thetas = grid_ref[idx_top]
        
        best_local_th, best_local_cvar = RobustSIP.verify_continuous_cvar(w_opt, X_train, Y_train, H, tau, top_thetas, bounds_v, bounds_d)
        
        rho, _, _ = RobustSIP.compute_dispersion_certificate(bounds_v, bounds_d, n_v, n_d, H, X_train, tau)
        
        push!(res_df, (
            labels[i],
            max_grad_norm,
            rho,
            max_grad_norm * rho,
            max(0.0, best_local_cvar - val_21)
        ))
    end
    
    CSV.write(joinpath(output_dir, "gap_verification.csv"), res_df)
    println("Saved gap_verification.csv")
end

if abspath(PROGRAM_FILE) == @__FILE__
    run_gap_verification()
end
