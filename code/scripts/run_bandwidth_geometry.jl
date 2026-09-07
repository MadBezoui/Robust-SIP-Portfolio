# Bandwidth orientation: diagonal versus full covariance bandwidth matrix.
#
# The baseline uses a diagonal bandwidth, H_diag = T^(-1/3) * diag(var(logVIX),
# var(Drawdown)), even though the two state variables are correlated. The scale
# of the bandwidth is already tested elsewhere; this experiment tests its
# orientation, comparing H_diag with the full-covariance rule
#
#     H_full = T^(-1/3) * Sigma_y,
#
# which carries the same scaling and adds only the off-diagonal term. Everything
# else -- estimation window, holding period, weight cap, return target, state
# grid and transaction costs -- is identical to 01_run_backtest.jl, so the two
# runs differ in the kernel geometry alone.

using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf

include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

const OUT = normpath(joinpath(@__DIR__, "..", "results"))

function run_geometry(kind::String, X_all, Y_all;
                      trans_cost=0.0010, tau=0.05, window_size=1260,
                      step_size=21, max_weight=0.15)
    T_total, N = size(X_all)
    rets, turns = Union{Float64,Missing}[], Union{Float64,Missing}[]
    whist = Any[]
    ess_means, n_active, worst_vals, corrs = Float64[], Float64[], Float64[], Float64[]
    prev_growth = nothing
    t_start = 1
    while t_start + window_size + step_size - 1 <= T_total
        t_end = t_start + window_size - 1
        hs, he = t_end + 1, t_end + step_size

        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        mu_train = mean(X_train, dims=1)[:] * 252.0
        n_train = size(Y_train, 1)
        push!(corrs, cor(Y_train[:, 1], Y_train[:, 2]))

        H = if kind == "diag"
            h_v = std(Y_train[:, 1]) * n_train^(-1/6)
            h_d = std(Y_train[:, 2]) * n_train^(-1/6)
            [h_v^2 0.0; 0.0 h_d^2]
        elseif kind == "full"
            Sigma = cov(Y_train)
            Hf = n_train^(-1/3) .* Sigma
            # guard against a numerically singular window
            Hf + 1e-12 * I(2)
        else
            error("unknown kind $kind")
        end

        v_lo, v_hi = extrema(Y_train[:, 1])
        d_lo, d_hi = extrema(Y_train[:, 2])
        dv = 0.10 * (v_hi - v_lo)
        dd = 0.10 * (d_hi - d_lo)
        vg = range(v_lo - dv, v_hi + dv, length=21)
        dg = range(max(0.0, d_lo - dd), min(1.0, d_hi + dd), length=21)
        grid = [[v, d] for v in vg for d in dg]

        target = median(mu_train)
        w, lb, ub, active, _, _, _, _, _ = solve_robust_sip(
            X_train, Y_train, grid, H, mu_train ./ 252.0, tau,
            target / 252.0; max_weight=max_weight)

        if !(w === missing) && !any(ismissing.(w))
            push!(n_active, length(active))
            push!(worst_vals, ub * 100.0)
            if !isempty(active)
                e = [1.0 / sum(get_kernel_weights(Y_train, th, H).^2) for th in active]
                push!(ess_means, mean(e))
            end
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
     wealth = wl[end], ess = mean(ess_means), active = mean(n_active),
     worst = mean(worst_vals), corr = mean(corrs), nwin = length(r))
end

function main()
    df = CSV.read(joinpath(normpath(joinpath(@__DIR__, "..", "data")),
                           "aligned_market_data.csv"), DataFrame)
    cn = names(df); vix_idx = findfirst(==("VIX"), cn)
    rc = cn[2:(vix_idx - 1)]
    X_all = Matrix{Float64}(df[:, rc])[2:end, :]
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])[1:end-1, :]

    out = DataFrame(Geometry=String[], Ann_Return=Float64[], Ann_Vol=Float64[],
                    Sharpe=Float64[], Max_DD=Float64[], Turnover=Float64[],
                    Final_Wealth=Float64[], Mean_Active_ESS=Float64[],
                    Mean_Active_States=Float64[], Mean_Worst_CVaR=Float64[],
                    Mean_State_Corr=Float64[], N_Windows=Int[])
    for k in ("diag", "full")
        println("bandwidth geometry = $k")
        r = run_geometry(k, X_all, Y_all)
        push!(out, (k, r.ann, r.vol, r.sharpe, r.mdd, r.turn, r.wealth,
                    r.ess, r.active, r.worst, r.corr, r.nwin))
        println("   Sharpe $(round(r.sharpe,digits=3))  worst CVaR $(round(r.worst,digits=4))%  " *
                "active $(round(r.active,digits=2))  ESS $(round(r.ess,digits=1))  " *
                "turnover $(round(r.turn*100,digits=2))%")
        flush(stdout)
    end
    CSV.write(joinpath(OUT, "bandwidth_geometry.csv"), out)
    show(out, allrows=true, allcols=true)
end

main()
