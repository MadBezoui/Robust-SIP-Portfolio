using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, LinearAlgebra

output_dir = normpath(joinpath(@__DIR__, "..", "results"))
df = CSV.read(normpath(joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")), DataFrame)

col_names = names(df)
vix_idx = findfirst(x -> x == "VIX", col_names)
returns_cols = col_names[2:(vix_idx - 1)]

X_raw = Matrix{Float64}(df[:, returns_cols])
X_all = X_raw[2:end, :]

T_total, N = size(X_all)
holding_period = 21
window_size = 252

for s in ["CondCVaR", "RobustSIP_Hull"]
    w_file = joinpath(output_dir, "weights_$(s).csv")
    if !isfile(w_file)
        println("Missing \$w_file")
        continue
    end
    df_w = CSV.read(w_file, DataFrame)
    
    dates = df_w.Date
    w_mat = Matrix(df_w[:, 2:end])
    
    n_periods = length(dates)
    ret_gross = zeros(n_periods)
    ret_net = zeros(n_periods)
    turnovers = zeros(n_periods)
    
    w_prev = fill(1.0/N, N)
    
    for i in 1:n_periods
        rebal_date = dates[i]
        idx = findfirst(==(rebal_date), df.Date) # This is the index in df. So it corresponds to idx-1 in X_all.
        if idx === nothing
            continue
        end
        # The holding period returns are X_all[idx-1 : idx-1+holding_period-1]
        start_idx = idx - 1
        end_idx = start_idx + holding_period - 1
        if end_idx > T_total
            continue
        end
        
        w_current = w_mat[i, :]
        turnovers[i] = sum(abs.(w_current .- w_prev)) / 2.0
        
        # Calculate compounded holding period return
        # The period returns are X_all[start_idx:end_idx, :]
        wealth = w_current
        for t in start_idx:end_idx
            wealth = wealth .* (1.0 .+ X_all[t, :])
        end
        
        gross = sum(wealth) - 1.0
        ret_gross[i] = gross
        ret_net[i] = gross - turnovers[i] * 0.0010 # 10 bps
        
        w_end = wealth ./ sum(wealth)
        w_prev = w_end
    end
    
    df_perf = DataFrame(Date=dates, Return_Gross=ret_gross, Turnover=turnovers, Return=ret_net)
    CSV.write(joinpath(output_dir, "perf_\$(s).csv"), df_perf)
    println("Saved perf_\$(s).csv")
end
