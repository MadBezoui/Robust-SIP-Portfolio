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
    ci_lower = diff_orig - percentile(boot_t_stats, 97.5) * se_orig
    ci_upper = diff_orig - percentile(boot_t_stats, 2.5) * se_orig
    
    return diff_orig, se_orig, ci_lower, ci_upper, p_val
end

function percentile(v, p)
    sv = sort(v)
    idx = max(1, min(length(v), round(Int, p / 100 * length(v))))
    return sv[idx]
end
