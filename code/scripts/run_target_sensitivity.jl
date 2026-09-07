# Sensitivity of the rolling experiment to the expected-return target.
#
# The baseline sets the target to the cross-sectional median of the estimated
# annualised asset means. The manuscript notes that the higher volatility and
# concentration of Robust SIP may come from the interaction of return targeting,
# state conditioning and boundary effects, and leaves that question open. This
# experiment separates the two: it repeats the full rolling experiment with the
# return constraint at Q25, Q50 (the baseline) and Q75 of the estimated means,
# and once with the constraint made non-binding, holding everything else --
# estimation window, holding period, weight cap, bandwidth rule, state grid and
# transaction costs -- exactly as in 01_run_backtest.jl.
#
# "Unconstrained" sets the target to the minimum attainable portfolio mean under
# the weight cap, so the constraint is present but never active.

using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf

include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

const OUT = normpath(joinpath(@__DIR__, "..", "results"))

function run_target(spec::String, X_all, Y_all;
                    trans_cost=0.0010, tau=0.05, window_size=1260,
                    step_size=21, max_weight=0.15)
    T_total, N = size(X_all)
    rets, turns = Union{Float64,Missing}[], Union{Float64,Missing}[]
    whist = Any[]
    ena, n_active, worst_vals = Float64[], Float64[], Float64[]
    prev_growth = nothing
    t_start = 1
    while t_start + window_size + step_size - 1 <= T_total
        t_end = t_start + window_size - 1
        hs, he = t_end + 1, t_end + step_size

        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        mu_train = mean(X_train, dims=1)[:] * 252.0

        n_train = size(Y_train, 1)
        h_v = std(Y_train[:, 1]) * n_train^(-1/6)
        h_d = std(Y_train[:, 2]) * n_train^(-1/6)
        H = [h_v^2 0.0; 0.0 h_d^2]

        v_lo, v_hi = extrema(Y_train[:, 1])
        d_lo, d_hi = extrema(Y_train[:, 2])
        dv = 0.10 * (v_hi - v_lo)
        dd = 0.10 * (d_hi - d_lo)
        vg = range(v_lo - dv, v_hi + dv, length=21)
        dg = range(max(0.0, d_lo - dd), min(1.0, d_hi + dd), length=21)
        grid = [[v, d] for v in vg for d in dg]

        # the four specifications, all on the annualised scale of mu_train
        target = if spec == "none"
            min_feasible_return(mu_train, max_weight)
        elseif spec == "Q25"
            quantile(mu_train, 0.25)
        elseif spec == "Q50"
            median(mu_train)
        elseif spec == "Q75"
            quantile(mu_train, 0.75)
        else
            error("unknown spec $spec")
        end

        w, lb, ub, active, _, _, _, _, _ = solve_robust_sip(
            X_train, Y_train, grid, H, mu_train ./ 252.0, tau,
            target / 252.0; max_weight=max_weight)

        if !(w === missing) && !any(ismissing.(w))
            push!(n_active, length(active))
            push!(worst_vals, ub * 100.0)
            wv0 = Vector{Float64}(w)
            push!(ena, 1.0 / sum(wv0 .^ 2))
        end

        growth = vec(prod(1.0 .+ X_all[hs:he, :], dims=1))
        if w === missing || any(ismissing.(w))
            push!(whist, w); push!(turns, missing); push!(rets, missing)
        else
            wv = Vector{Float64}(w)
            if !isempty(whist) && prev_growth !== nothing && !any(ismissing.(whist[end]))
                dr = Vector{Float64}(whist[end]) .* prev_growth
                w_pre = dr ./ sum(dr)
            else
                w_pre = fill(1.0 / N, N)
            end
            to = 0.5 * sum(abs.(wv .- w_pre))
            push!(turns, to); push!(rets, sum(wv .* (growth .- 1.0)) - trans_cost * to)
            push!(whist, wv)
        end
        prev_growth = growth
        t_start += step_size
    end

    r = collect(skipmissing(rets))
    wl = vcat(1.0, cumprod(1.0 .+ r))
    (ann = mean(r) * 12.0, vol = std(r) * sqrt(12.0),
     sharpe = mean(r) * 12.0 / (std(r) * sqrt(12.0)),
     mdd = minimum(wl ./ accumulate(max, wl) .- 1.0),
     turn = mean(collect(skipmissing(turns))),
     wealth = wl[end], ena = mean(ena), active = mean(n_active),
     worst = mean(worst_vals), nwin = length(r))
end

function main()
    df = CSV.read(joinpath(normpath(joinpath(@__DIR__, "..", "data")),
                           "aligned_market_data.csv"), DataFrame)
    cn = names(df); vix_idx = findfirst(==("VIX"), cn)
    rc = cn[2:(vix_idx - 1)]
    X_all = Matrix{Float64}(df[:, rc])[2:end, :]
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])[1:end-1, :]

    out = DataFrame(Target=String[], Ann_Return=Float64[], Ann_Vol=Float64[],
                    Sharpe=Float64[], Max_DD=Float64[], Turnover=Float64[],
                    Final_Wealth=Float64[], Mean_ENA=Float64[],
                    Mean_Active_States=Float64[], Mean_Worst_CVaR=Float64[],
                    N_Windows=Int[])
    for s in ("none", "Q25", "Q50", "Q75")
        println("target = $s")
        r = run_target(s, X_all, Y_all)
        push!(out, (s, r.ann, r.vol, r.sharpe, r.mdd, r.turn, r.wealth,
                    r.ena, r.active, r.worst, r.nwin))
        println("   Sharpe $(round(r.sharpe,digits=3))  vol $(round(r.vol*100,digits=2))%  " *
                "ENA $(round(r.ena,digits=2))  turnover $(round(r.turn*100,digits=2))%")
    end
    CSV.write(joinpath(OUT, "target_sensitivity.csv"), out)
    show(out, allrows=true, allcols=true)
end

main()
