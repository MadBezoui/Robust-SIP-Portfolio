# Two additional benchmarks requested by the referee, computed on exactly the
# same rolling calendar and with exactly the same estimation settings as
# 01_run_backtest.jl, so that they are directly comparable with Table 4.
#
#   Convex-Hull Robust SIP  (Major Comment 2): the candidate grid is restricted
#       to the empirical convex hull of the training states, so the worst-case
#       is taken only over states the data actually support.
#   State-Conditioned CVaR  (Major Comment 3): nominal CVaR under the
#       kernel-weighted conditional distribution at the current state y_T, with
#       no robustness over the state domain.
#
# The only differences from the baseline are the separation set (hull) and the
# absence of the robust layer (conditional). Window length, holding period,
# weight cap, return target, bandwidth rule and transaction costs are identical.

using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf

include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

const OUT = normpath(joinpath(@__DIR__, "..", "results"))

# The module ships an LP-based hull membership test (one LP with T variables per
# candidate point). In two dimensions the same question is answered exactly and
# far faster by building the hull once per window and testing point inclusion,
# which is what makes this experiment tractable over 377 windows.
cross(o, a, b) = (a[1]-o[1])*(b[2]-o[2]) - (a[2]-o[2])*(b[1]-o[1])

function convex_hull_2d(P::Vector{Vector{Float64}})
    pts = sort(unique(P), by = p -> (p[1], p[2]))
    length(pts) <= 2 && return pts
    lower = Vector{Vector{Float64}}()
    for p in pts
        while length(lower) >= 2 && cross(lower[end-1], lower[end], p) <= 0
            pop!(lower)
        end
        push!(lower, p)
    end
    upper = Vector{Vector{Float64}}()
    for p in reverse(pts)
        while length(upper) >= 2 && cross(upper[end-1], upper[end], p) <= 0
            pop!(upper)
        end
        push!(upper, p)
    end
    vcat(lower[1:end-1], upper[1:end-1])
end

function in_hull(pt::Vector{Float64}, hull::Vector{Vector{Float64}}; tol=1e-12)
    n = length(hull)
    n < 3 && return false
    for i in 1:n
        if cross(hull[i], hull[mod1(i+1, n)], pt) < -tol
            return false
        end
    end
    true
end

function hull_filter(grid::Vector{Vector{Float64}}, Y::Matrix{Float64})
    hull = convex_hull_2d([Y[i, :] for i in 1:size(Y, 1)])
    [g for g in grid if in_hull(g, hull)]
end

function run_referee_benchmarks(trans_cost::Float64=0.0010, tau::Float64=0.05)
    df = CSV.read(joinpath(normpath(joinpath(@__DIR__, "..", "data")),
                           "aligned_market_data.csv"), DataFrame)
    cn = names(df)
    vix_idx = findfirst(==("VIX"), cn)
    returns_cols = cn[2:(vix_idx - 1)]

    X_all = Matrix{Float64}(df[:, returns_cols])[2:end, :]
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])[1:end-1, :]
    dates_all = df.Date[2:end]

    T_total, N = size(X_all)
    window_size = 1260          # identical to the baseline
    step_size   = 21
    max_weight  = 0.15

    strategies = ["RobustSIP_Hull", "CondCVaR"]
    rets  = Dict(s => Union{Float64,Missing}[] for s in strategies)
    turns = Dict(s => Union{Float64,Missing}[] for s in strategies)
    whist = Dict(s => Any[] for s in strategies)
    hull_frac = Float64[]
    dates_out = String[]

    prev_growth = nothing
    step = 0
    t_start = 1
    while t_start + window_size + step_size - 1 <= T_total
        t_end = t_start + window_size - 1
        hs, he = t_end + 1, t_end + step_size
        step += 1

        X_train = X_all[t_start:t_end, :]
        Y_train = Y_all[t_start:t_end, :]
        mu_train = mean(X_train, dims=1)[:] * 252.0

        # identical bandwidth rule
        n_train = size(Y_train, 1)
        h_vix = std(Y_train[:, 1]) * n_train^(-1/6)
        h_dd  = std(Y_train[:, 2]) * n_train^(-1/6)
        H = [h_vix^2 0.0; 0.0 h_dd^2]

        # identical candidate grid
        vix_min, vix_max = extrema(Y_train[:, 1])
        dd_min,  dd_max  = extrema(Y_train[:, 2])
        dv = 0.10 * (vix_max - vix_min)
        dd = 0.10 * (dd_max - dd_min)
        vix_grid = range(vix_min - dv, vix_max + dv, length=21)
        dd_grid  = range(max(0.0, dd_min - dd), min(1.0, dd_max + dd), length=21)
        grid_thetas = [[v, d] for v in vix_grid for d in dd_grid]

        target_return = median(mu_train)

        # --- Major Comment 2: restrict the separation set to the empirical hull
        hull_thetas = hull_filter(grid_thetas, Y_train)
        isempty(hull_thetas) && (hull_thetas = grid_thetas)
        push!(hull_frac, length(hull_thetas) / length(grid_thetas))
        w_hull, _, _, _, _, _, _, _, _ = solve_robust_sip(
            X_train, Y_train, hull_thetas, H, mu_train ./ 252.0, tau,
            target_return / 252.0; max_weight=max_weight)

        # --- Major Comment 3: nominal CVaR conditioned on the current state
        theta_now = Y_train[end, :]
        w_cond, _, _ = solve_conditional_cvar(
            X_train, Y_train, theta_now, H, mu_train ./ 252.0, tau,
            target_return / 252.0, max_weight)

        X_test = X_all[hs:he, :]
        growth = vec(prod(1.0 .+ X_test, dims=1))

        for (s, w_new) in (("RobustSIP_Hull", w_hull), ("CondCVaR", w_cond))
            if w_new === missing || any(ismissing.(w_new))
                push!(whist[s], w_new); push!(turns[s], missing); push!(rets[s], missing)
                continue
            end
            w = Vector{Float64}(w_new)
            if !isempty(whist[s]) && prev_growth !== nothing && !any(ismissing.(whist[s][end]))
                drifted = Vector{Float64}(whist[s][end]) .* prev_growth
                w_pre = drifted ./ sum(drifted)
            else
                w_pre = fill(1.0 / N, N)
            end
            to = 0.5 * sum(abs.(w .- w_pre))
            push!(turns[s], to)
            push!(rets[s], sum(w .* (growth .- 1.0)) - trans_cost * to)
            push!(whist[s], w)
        end

        push!(dates_out, string(dates_all[he]))
        prev_growth = growth
        t_start += step_size
        step % 25 == 0 && println("  window $step ($(dates_all[he]))")
    end

    out = DataFrame(Date = dates_out)
    for s in strategies
        out[!, Symbol(s * "_Ret")] = rets[s]
        out[!, Symbol(s * "_TO")]  = turns[s]
    end
    CSV.write(joinpath(OUT, "referee_benchmarks_returns.csv"), out)

    summary = DataFrame(Strategy=String[], Ann_Mean=Float64[], Ann_Vol=Float64[],
                        Sharpe=Float64[], Max_DD=Float64[], Avg_Turnover=Float64[],
                        Final_Wealth=Float64[])
    for s in strategies
        r = collect(skipmissing(rets[s]))
        w = vcat(1.0, cumprod(1.0 .+ r))
        ddw = minimum(w ./ accumulate(max, w) .- 1.0)
        push!(summary, (s, mean(r) * 12.0, std(r) * sqrt(12.0),
                        mean(r) * 12.0 / (std(r) * sqrt(12.0)), ddw,
                        mean(collect(skipmissing(turns[s]))), w[end]))
    end
    CSV.write(joinpath(OUT, "referee_benchmarks_summary.csv"), summary)
    open(joinpath(OUT, "hull_retained_fraction.txt"), "w") do f
        println(f, mean(hull_frac))
    end
    println("\n$(length(dates_out)) windows, $(dates_out[1]) to $(dates_out[end])")
    println("mean hull-retained grid fraction: $(round(mean(hull_frac), digits=4))")
    show(summary, allrows=true, allcols=true)
end

run_referee_benchmarks()
