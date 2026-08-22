using CSV, DataFrames, Statistics, Random

function run_statistical_inference()

output_dir = "../results"
ts_df = CSV.read(joinpath(output_dir, "strategy_holding_period_returns.csv"), DataFrame)

# Calculate Sharpe Ratio given a return series (annualized)
function calc_sr(rets)
    v = collect(skipmissing(rets))
    return (mean(v) / std(v)) * sqrt(12.0)
end

function percentile(v, p)
    sv = sort(v)
    idx = max(1, min(length(v), round(Int, p / 100 * length(v))))
    return sv[idx]
end

"""
Paired circular block percentile bootstrap for Sharpe-ratio differences.
We explicitly align the non-missing pairs before bootstrapping.
The p-value is computed by centering the bootstrap distribution and calculating 
the symmetric tail probability of the centered distribution evaluating beyond the original estimate.
"""
function paired_circular_block_percentile_bootstrap(r1_in::AbstractVector, r2_in::AbstractVector, block_size::Int=12, n_reps::Int=5000; seed::Int=20260814)
    Random.seed!(seed)
    
    # Extract complete paired observations
    valid_idx = findall(.!ismissing.(r1_in) .& .!ismissing.(r2_in))
    r1 = Float64.(r1_in[valid_idx])
    r2 = Float64.(r2_in[valid_idx])
    T = length(r1)
    
    diff_sharpe_orig = calc_sr(skipmissing(r1_in)) - calc_sr(skipmissing(r2_in))
    
    boot_diffs = Float64[]
    for b in 1:n_reps
        start_indices = rand(1:T, div(T, block_size) + 1)
        boot_idx = Int[]
        for s in start_indices
            append!(boot_idx, [mod1(s + i - 1, T) for i in 1:block_size])
        end
        boot_idx = boot_idx[1:T]
        
        samp1 = r1[boot_idx]
        samp2 = r2[boot_idx]
        
        ds_ann = calc_sr(samp1) - calc_sr(samp2)
        push!(boot_diffs, ds_ann)
    end
    
    ci_lower = percentile(boot_diffs, 2.5)
    ci_upper = percentile(boot_diffs, 97.5)
    boot_se = std(boot_diffs)
    
    # Centered percentile bootstrap p-value
    centered_boot = boot_diffs .- mean(boot_diffs)
    p_val = (1.0 + sum(abs.(centered_boot) .>= abs(diff_sharpe_orig))) / (n_reps + 1.0)
    
    return diff_sharpe_orig, boot_se, ci_lower, ci_upper, p_val, boot_diffs
end

println("Computing paired circular block percentile bootstrap inference (B=5000)...")
boot_res_df = DataFrame(
    Benchmark=String[], Sharpe_Diff=Float64[], Std_Error=Float64[],
    CI_Lower_95=Float64[], CI_Upper_95=Float64[], P_Value=Float64[]
)

main_boot_dist = Float64[]
rets_rob = ts_df.RobustSIP_Ret

for bench in ["NominalCVaR", "1/N", "MinVar", "FiniteRegime"]
    bench_col = bench == "1/N" ? "1/N_Ret" : bench * "_Ret"
    diff, se, ci_l, ci_u, p_val, boot_dist = paired_circular_block_percentile_bootstrap(
        rets_rob, ts_df[!, bench_col], 12, 5000; seed=20260814
    )
    push!(boot_res_df, (bench, diff, se, ci_l, ci_u, p_val))
    if bench == "NominalCVaR"
        global main_boot_dist = boot_dist
    end
end
CSV.write(joinpath(output_dir, "bootstrap_inference.csv"), boot_res_df)
CSV.write(joinpath(output_dir, "bootstrap_distribution.csv"), DataFrame(Bootstrap_Diff=main_boot_dist))
println("Saved bootstrap_inference.csv and bootstrap_distribution.csv")
display(boot_res_df)

println("\nComputing Block Length Sensitivity...")
block_lengths = [6, 9, 12, 18, 24]
boot_sens_df = DataFrame(Block_Length=Int[], P_Value=Float64[], SE=Float64[])

for b in block_lengths
    _, se, _, _, p_val, _ = paired_circular_block_percentile_bootstrap(
        rets_rob, ts_df[!, "NominalCVaR_Ret"], b, 5000; seed=20260814
    )
    push!(boot_sens_df, (b, p_val, se))
end
CSV.write(joinpath(output_dir, "block_length_sensitivity.csv"), boot_sens_df)
println("Saved block_length_sensitivity.csv")
display(boot_sens_df)

end
