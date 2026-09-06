using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra

include(joinpath(@__DIR__, "..", "src", "RobustSIP.jl"))
using .RobustSIP

# Load Data
df = CSV.read(normpath(joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")), DataFrame)
calendar_df = CSV.read(normpath(joinpath(@__DIR__, "..", "results", "calendar.csv")), DataFrame)

vix_idx = findfirst(x -> x == "VIX", names(df))
returns_cols = names(df)[2:(vix_idx - 1)]

X_raw = Matrix{Float64}(df[:, returns_cols])
Y_raw_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])
dates_raw = df.Date

X_all = X_raw[2:end, :]
Y_all = Y_raw_all[1:end-1, :]
dates_all = dates_raw[2:end]

function run_ablation(state_mode, H_mode)
    T_total, N = size(X_all)
    window_size = 1260
    
    daily_rets = zeros(0)
    for i in 1:nrow(calendar_df)
        train_end_date = calendar_df.Train_End_Date[i]
        t_end = findfirst(==(train_end_date), dates_all)
        t_start = t_end - window_size + 1
        
        X_train = X_all[t_start:t_end, :]
        
        if state_mode == "VIX"
            Y_train = Y_all[t_start:t_end, 1:1]
        elseif state_mode == "DD"
            Y_train = Y_all[t_start:t_end, 2:2]
        else
            Y_train = Y_all[t_start:t_end, :]
        end
        
        # Bandwidth
        n_train = size(Y_train, 1)
        if H_mode == "Diagonal"
            if size(Y_train, 2) == 1
                H = (std(Y_train[:,1]) * n_train^(-1/5))^2 * ones(1,1)
            else
                H = [ (std(Y_train[:,1]) * n_train^(-1/6))^2 0.0; 0.0 (std(Y_train[:,2]) * n_train^(-1/6))^2 ]
            end
        elseif H_mode == "Full"
            H = cov(Y_train) * n_train^(-1/3)
        end
        
        # Grid
        if size(Y_train, 2) == 1
            min_y, max_y = minimum(Y_train[:,1]), maximum(Y_train[:,1])
            marg = 0.1 * (max_y - min_y)
            grid = [[x] for x in range(min_y - marg, max_y + marg, length=21)]
        else
            min_vix, max_vix = minimum(Y_train[:,1]), maximum(Y_train[:,1])
            min_dd, max_dd = minimum(Y_train[:,2]), maximum(Y_train[:,2])
            mv = 0.1 * (max_vix - min_vix)
            md = 0.1 * (max_dd - min_dd)
            gv = range(min_vix - mv, max_vix + mv, length=11)
            gd = range(min_dd - md, max_dd + md, length=11)
            grid = [[v, d] for v in gv, d in gd]
            grid = reshape(grid, :)
        end
        
        mu_train = vec(mean(X_train, dims=1))
        t_ret = maximum(mu_train) * 0.50
        
        try
            w, _, _, _ = solve_robust_sip(X_train, Y_train, grid, H, mu_train, 0.05, t_ret, 0.15)
            # Eval out of sample
            h_start = findfirst(==(calendar_df.Hold_Start_Date[i]), dates_all)
            h_end = findfirst(==(calendar_df.Hold_End_Date[i]), dates_all)
            
            shares = copy(w)
            for t in h_start:h_end
                r_t = X_all[t, :]
                push!(daily_rets, dot(shares, 1.0 .+ r_t) - 1.0)
                shares = shares .* (1.0 .+ r_t)
                if sum(shares) > 0
                    shares ./= sum(shares)
                end
            end
        catch
            h_start = findfirst(==(calendar_df.Hold_Start_Date[i]), dates_all)
            h_end = findfirst(==(calendar_df.Hold_End_Date[i]), dates_all)
            for t in h_start:h_end
                push!(daily_rets, 0.0) # flat if error
            end
        end
    end
    
    ann_ret = mean(daily_rets) * 252.0
    ann_vol = std(daily_rets) * sqrt(252.0)
    sharpe = ann_ret / ann_vol
    
    losses = -daily_rets
    sl = sort(losses, rev=true)
    k = floor(Int, 0.05 * length(sl))
    es95 = mean(sl[1:k])
    
    return es95, sharpe
end

res = DataFrame(State_Model=String[], OOS_ES95=Float64[], Sharpe=Float64[])

println("Running VIX-only...")
es, sh = run_ablation("VIX", "Diagonal")
push!(res, ("VIX-only state-robust CVaR", es, sh))

println("Running DD-only...")
es, sh = run_ablation("DD", "Diagonal")
push!(res, ("Drawdown-only state-robust CVaR", es, sh))

println("Running Full Covariance VIX+DD...")
es, sh = run_ablation("Both", "Full")
push!(res, ("VIX + DD (Full covariance)", es, sh))

CSV.write("results/experiment_5_ablation.csv", res)
println("Done ablation.")
