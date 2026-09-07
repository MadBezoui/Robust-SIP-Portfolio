# A regularized state-conditioned CVaR comparator.
#
# The state-conditioned benchmark of run_referee_benchmarks.jl reweights the
# training sample by the Nadaraya-Watson kernel at the current state y_T. When
# the effective sample size at that state is small the resulting prescription is
# very unstable, which makes it an easy comparator to beat. A fairer and
# stronger comparator shrinks the conditional law towards the unconditional one,
#
#     p^(lambda) = (1 - lambda) * (1/T) + lambda * p_kernel(y_T),
#
# and then solves a nominal CVaR problem under p^(lambda). lambda = 0 recovers
# the unconditional empirical CVaR and lambda = 1 the pure conditional
# prescription, so the family interpolates between the two benchmarks already in
# the paper and isolates the value added by the robust layer from the value
# added by conditioning alone.
#
# The rolling calendar and every estimation setting are identical to
# 01_run_backtest.jl, so the results are directly comparable with Table 4.

using Pkg
Pkg.activate(normpath(joinpath(@__DIR__, "..")))
using CSV, DataFrames, Dates, Statistics, LinearAlgebra, Printf
using JuMP, HiGHS

include(normpath(joinpath(@__DIR__, "..", "src", "RobustSIP.jl")))
using .RobustSIP

const OUT = normpath(joinpath(@__DIR__, "..", "results"))

# Nominal CVaR under an arbitrary scenario probability vector. This is the same
# LP as solve_conditional_cvar in the module, with the probabilities supplied by
# the caller instead of being recomputed from a single state.
function solve_cvar_under_p(X::Matrix{Float64}, p::Vector{Float64},
                            mu::Vector{Float64}, tau::Float64,
                            target_return::Float64, max_weight::Float64)
    T, N = size(X)
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    t_ret = clamp(target_return, mu_min, mu_max - 1e-6)

    model = Model(HiGHS.Optimizer); set_silent(model)
    @variable(model, t_var)
    @variable(model, 0.0 <= w[1:N] <= max_weight)
    @variable(model, z)
    @variable(model, u[1:T] >= 0.0)
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= t_ret)
    @constraint(model, z + (1.0 / tau) * sum(p[i] * u[i] for i in 1:T) <= t_var)
    for i in 1:T
        @constraint(model, u[i] >= -dot(X[i, :], w) - z)
    end
    @objective(model, Min, t_var)
    optimize!(model)
    st = termination_status(model)
    (st == MOI.OPTIMAL || st == MOI.LOCALLY_SOLVED) ? value.(w) : missing
end

function main(; trans_cost=0.0010, tau=0.05, window_size=1260,
                step_size=21, max_weight=0.15)
    df = CSV.read(joinpath(normpath(joinpath(@__DIR__, "..", "data")),
                           "aligned_market_data.csv"), DataFrame)
    cn = names(df); vix_idx = findfirst(==("VIX"), cn)
    rc = cn[2:(vix_idx - 1)]
    X_all = Matrix{Float64}(df[:, rc])[2:end, :]
    Y_all = Matrix{Float64}(df[:, ["logVIX", "Drawdown"]])[1:end-1, :]

    T_total, N = size(X_all)
    lambdas = [0.0, 0.25, 0.50, 0.75, 1.0]
    rets  = Dict(l => Union{Float64,Missing}[] for l in lambdas)
    turns = Dict(l => Union{Float64,Missing}[] for l in lambdas)
    whist = Dict(l => Any[] for l in lambdas)
    ess_at_state = Float64[]

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

        n_train = size(Y_train, 1)
        h_v = std(Y_train[:, 1]) * n_train^(-1/6)
        h_d = std(Y_train[:, 2]) * n_train^(-1/6)
        H = [h_v^2 0.0; 0.0 h_d^2]

        theta_now = Y_train[end, :]
        p_ker = get_kernel_weights(Y_train, theta_now, H)
        push!(ess_at_state, 1.0 / sum(p_ker .^ 2))
        p_unc = fill(1.0 / n_train, n_train)
        target = median(mu_train)

        growth = vec(prod(1.0 .+ X_all[hs:he, :], dims=1))

        for l in lambdas
            p = (1.0 - l) .* p_unc .+ l .* p_ker
            p ./= sum(p)
            w_new = solve_cvar_under_p(X_train, p, mu_train ./ 252.0, tau,
                                       target / 252.0, max_weight)
            if w_new === missing
                push!(whist[l], missing); push!(turns[l], missing); push!(rets[l], missing)
                continue
            end
            w = Vector{Float64}(w_new)
            if !isempty(whist[l]) && prev_growth !== nothing && !(whist[l][end] === missing)
                dr = Vector{Float64}(whist[l][end]) .* prev_growth
                w_pre = dr ./ sum(dr)
            else
                w_pre = fill(1.0 / N, N)
            end
            to = 0.5 * sum(abs.(w .- w_pre))
            push!(turns[l], to)
            push!(rets[l], sum(w .* (growth .- 1.0)) - trans_cost * to)
            push!(whist[l], w)
        end
        prev_growth = growth
        t_start += step_size
        step % 50 == 0 && println("  window $step")
    end

    summary = DataFrame(Lambda=Float64[], Ann_Return=Float64[], Ann_Vol=Float64[],
                        Sharpe=Float64[], Max_DD=Float64[], Turnover=Float64[],
                        Final_Wealth=Float64[], N_Windows=Int[])
    for l in lambdas
        r = collect(skipmissing(rets[l]))
        wl = vcat(1.0, cumprod(1.0 .+ r))
        push!(summary, (l, mean(r) * 12.0, std(r) * sqrt(12.0),
                        mean(r) * 12.0 / (std(r) * sqrt(12.0)),
                        minimum(wl ./ accumulate(max, wl) .- 1.0),
                        mean(collect(skipmissing(turns[l]))), wl[end], length(r)))
    end
    CSV.write(joinpath(OUT, "shrinkage_benchmark.csv"), summary)
    open(joinpath(OUT, "shrinkage_mean_ess.txt"), "w") do f
        println(f, mean(ess_at_state))
    end
    println("\nmean ESS at the current state: $(round(mean(ess_at_state), digits=1))")
    show(summary, allrows=true, allcols=true)
end

main()
