using CSV, DataFrames, Statistics, Random

output_dir = "../results"
ts_df = CSV.read(joinpath(output_dir, "strategy_monthly_returns.csv"), DataFrame)
rets_rob = ts_df.RobustSIP_Ret

function paired_circular_block_bootstrap(rets1::Vector{Float64}, rets2::Vector{Float64}, block_size::Int=12, n_reps::Int=5000; seed::Int=20260814)
    Random.seed!(seed)
    T = length(rets1)
    
    sr1_ann = (mean(rets1) / std(rets1)) * sqrt(12.0)
    sr2_ann = (mean(rets2) / std(rets2)) * sqrt(12.0)
    diff_sharpe_orig = sr1_ann - sr2_ann
    
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
        
        ds_ann = sqrt(12.0) * ((mean(samp1) / std(samp1)) - (mean(samp2) / std(samp2)))
        push!(boot_diffs, ds_ann)
    end
    
    function percentile(v, p)
        sv = sort(v)
        idx = max(1, min(length(v), round(Int, p / 100 * length(v))))
        return sv[idx]
    end

    ci_lower = percentile(boot_diffs, 2.5)
    ci_upper = percentile(boot_diffs, 97.5)
    boot_se = std(boot_diffs)
    
    centered_boot = boot_diffs .- mean(boot_diffs)
    p_val = (1.0 + sum(abs.(centered_boot) .>= abs(diff_sharpe_orig))) / (n_reps + 1.0)
    
    return diff_sharpe_orig, boot_se, ci_lower, ci_upper, p_val, boot_diffs
end

println("Computing circular moving-block bootstrap inference (B=5000)...")
boot_res_df = DataFrame(
    Benchmark=String[], Sharpe_Diff=Float64[], Std_Error=Float64[],
    CI_Lower_95=Float64[], CI_Upper_95=Float64[], P_Value=Float64[]
)
main_boot_dist = Float64[]
for bench in ["NominalCVaR", "1/N", "MinVar", "FiniteRegime"]
    diff, se, ci_l, ci_u, p_val, boot_dist = paired_circular_block_bootstrap(
        rets_rob, ts_df[!, Symbol(bench * "_Ret")], 12, 5000; seed=20260814
    )
    push!(boot_res_df, (bench, diff, se, ci_l, ci_u, p_val))
    if bench == "NominalCVaR"
        main_boot_dist = boot_dist
    end
end
CSV.write(joinpath(output_dir, "bootstrap_inference.csv"), boot_res_df)
CSV.write(joinpath(output_dir, "bootstrap_distribution.csv"), DataFrame(Bootstrap_Diff=main_boot_dist))

println("Computing Block Length Sensitivity...")
block_lengths = [6, 9, 12, 18, 24]
boot_sens_df = DataFrame(Block_Length=Int[], P_Value=Float64[], SE=Float64[])

function quick_boot_sens(r1, r2, b_len)
    Random.seed!(20260814)
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
    p_val = (1.0 + sum(abs.(boot_diffs .- mean(boot_diffs)) .>= abs(diff_orig))) / (5000 + 1.0)
    return p_val, std(boot_diffs)
end

for b in block_lengths
    p_val, se = quick_boot_sens(rets_rob, ts_df[!, :NominalCVaR_Ret], b)
    push!(boot_sens_df, (b, p_val, se))
end
CSV.write(joinpath(output_dir, "block_length_sensitivity.csv"), boot_sens_df)
println("Done.")
