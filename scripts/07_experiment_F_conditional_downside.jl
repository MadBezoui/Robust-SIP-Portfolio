using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra

data_path = normpath(joinpath(@__DIR__, "..", "data", "processed_state_return_pairs.csv"))
output_dir = normpath(joinpath(@__DIR__, "..", "results"))

df = CSV.read(data_path, DataFrame)
returns_cols = names(df)[2:31]
X_all = Matrix{Float64}(df[:, returns_cols])
dates_all = df.Date

# Read weights
strats = ["1N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]
strat_daily_rets = Dict{String, Vector{Float64}}()

calendar_df = CSV.read(joinpath(output_dir, "calendar.csv"), DataFrame)

for s in strats
    w_df = CSV.read(joinpath(output_dir, "weights_$(s).csv"), DataFrame)
    daily_rets = zeros(0)
    
    for i in 1:nrow(calendar_df)
        h_start = findfirst(==(calendar_df.Hold_Start_Date[i]), dates_all)
        h_end = findfirst(==(calendar_df.Hold_End_Date[i]), dates_all)
        
        w_start = Vector{Float64}(w_df[i, 1:30])
        shares = w_start # normalized initial shares at h_start
        
        for t in h_start:h_end
            ret_t = X_all[t, :]
            # value of portfolio at end of day t
            v_t = dot(shares, 1.0 .+ ret_t)
            push!(daily_rets, v_t - 1.0)
            
            # update shares for next day (constant shares = drifting weights)
            shares = shares .* (1.0 .+ ret_t)
            shares ./= sum(shares) # re-normalize to 1 for next day return calculation
        end
    end
    strat_daily_rets[s] = daily_rets
end

# Construct daily returns df
out_df = DataFrame(Date = Date[])
for i in 1:nrow(calendar_df)
    h_start = findfirst(==(calendar_df.Hold_Start_Date[i]), dates_all)
    h_end = findfirst(==(calendar_df.Hold_End_Date[i]), dates_all)
    append!(out_df.Date, dates_all[h_start:h_end])
end

for s in strats
    out_df[!, Symbol(s)] = strat_daily_rets[s]
end
CSV.write(joinpath(output_dir, "strategy_daily_returns.csv"), out_df)

# Now, conditional tail risk
# Match dates to state variables
df_state = innerjoin(out_df, df[:, [:Date, :logVIX, :Drawdown63]], on=:Date)
function cvar5(losses)
    isempty(losses) && return NaN
    sl = sort(losses, rev=true)
    k = max(1, floor(Int, 0.05 * length(losses)))
    return mean(sl[1:k])
end
function maxdd(rets)
    isempty(rets) && return NaN
    w = cumprod(1.0 .+ rets)
    rm = accumulate(max, w)
    return minimum(w ./ rm .- 1.0)
end

cond_res = DataFrame(State_Group=String[], Strategy=String[], CVaR_5=Float64[], Max_DD=Float64[], N_Days=Int[])
# Define groups
q_vix = quantile(df_state.logVIX, [0.33, 0.66, 0.90])
groups = [
    ("Low_VIX", df_state.logVIX .<= q_vix[1]),
    ("Med_VIX", (df_state.logVIX .> q_vix[1]) .& (df_state.logVIX .<= q_vix[2])),
    ("High_VIX", (df_state.logVIX .> q_vix[2]) .& (df_state.logVIX .<= q_vix[3])),
    ("Extreme_VIX", df_state.logVIX .> q_vix[3]),
    ("Crisis_DD", df_state.Drawdown63 .> 0.20)
]

for (gname, mask) in groups
    n_days = sum(mask)
    for s in strats
        rets = df_state[mask, Symbol(s)]
        push!(cond_res, (gname, s, cvar5(-rets), maxdd(rets), n_days))
    end
end
CSV.write(joinpath(output_dir, "conditional_tail_risk.csv"), cond_res)
println("Experiment F complete.")
