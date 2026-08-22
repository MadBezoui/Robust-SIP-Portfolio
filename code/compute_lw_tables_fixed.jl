using CSV
using DataFrames
using Statistics
using Random

df = CSV.read("results/strategy_holding_period_returns.csv", DataFrame)

function lw_studentized_bootstrap(rets1::Vector{Float64}, rets2::Vector{Float64}, block_size::Int=12, n_reps::Int=5000; seed::Int=20260821)
    Random.seed!(seed)
    T = length(rets1)
    
    sr1_ann = (mean(rets1) / std(rets1)) * sqrt(12.0)
    sr2_ann = (mean(rets2) / std(rets2)) * sqrt(12.0)
    diff_orig = sr1_ann - sr2_ann
    
    boot_t_stats = Float64[]
    boot_diffs = Float64[]
    
    for b in 1:n_reps
        start_indices = rand(1:T, div(T, block_size) + 1)
        boot_idx = Int[]
        for s in start_indices
            append!(boot_idx, [mod1(s + i - 1, T) for i in 1:block_size])
        end
        boot_idx = boot_idx[1:T]
        
        samp1 = rets1[boot_idx]
        samp2 = rets2[boot_idx]
        
        ds_boot = sqrt(12.0) * ((mean(samp1) / std(samp1)) - (mean(samp2) / std(samp2)))
        push!(boot_diffs, ds_boot)
        
        se_boot = std(samp1 - samp2) / sqrt(T)
        t_stat = (ds_boot - diff_orig) / (se_boot + 1e-8)
        push!(boot_t_stats, t_stat)
    end
    
    se_orig = std(rets1 - rets2) / sqrt(T)
    t_orig = diff_orig / se_orig
    p_val = (1.0 + sum(abs.(boot_t_stats) .>= abs(t_orig))) / (n_reps + 1.0)
    
    correct_se = std(boot_diffs)
    
    ci_lower = diff_orig - percentile(boot_t_stats, 97.5) * correct_se
    ci_upper = diff_orig - percentile(boot_t_stats, 2.5) * correct_se
    
    return diff_orig, correct_se, ci_lower, ci_upper, p_val, boot_diffs
end

function percentile(v, p)
    sv = sort(v)
    idx = max(1, min(length(v), round(Int, p / 100 * length(v))))
    return sv[idx]
end

println("--- Table 8 ---")
rob_ret = Vector{Float64}(collect(skipmissing(df.RobustSIP_Ret)))
for bench in ["NominalCVaR_Ret", "1/N_Ret", "MinVar_Ret", "FiniteRegime_Ret"]
    b_ret = Vector{Float64}(collect(skipmissing(df[!, bench])))
    min_len = min(length(rob_ret), length(b_ret))
    d, se, cl, cu, pv, _ = lw_studentized_bootstrap(rob_ret[1:min_len], b_ret[1:min_len])
    println("vs $bench: ΔSR=$(round(d, digits=4)), SE=$(round(se, digits=4)), CI=[$(round(cl, digits=4)), $(round(cu, digits=4))], p-val=$(round(pv, digits=3))")
end

println("\n--- Table 13 ---")
b_ret = Vector{Float64}(collect(skipmissing(df.NominalCVaR_Ret)))
min_len = min(length(rob_ret), length(b_ret))
_, _, _, _, _, boot_diffs = lw_studentized_bootstrap(rob_ret[1:min_len], b_ret[1:min_len], 12)
CSV.write("results/bootstrap_diffs_for_fig12.csv", DataFrame(boot_diffs=boot_diffs))

for b in [6, 9, 12, 18, 24]
    d, se, cl, cu, pv, _ = lw_studentized_bootstrap(rob_ret[1:min_len], b_ret[1:min_len], b)
    println("b=$b: SE=$(round(se, digits=4)), p-val=$(round(pv, digits=3))")
end
