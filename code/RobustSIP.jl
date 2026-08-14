module RobustSIP

using JuMP
using HiGHS
using LinearAlgebra
using Statistics
using Distributions

export get_kernel_weights, effective_sample_size, empirical_cvar, solve_master_cvar, solve_oracle, solve_robust_sip, solve_nominal_cvar, solve_min_variance, solve_finite_regime_cvar

"""
Gaussian Kernel Weight
"""
function get_kernel_weights(Y::Matrix{Float64}, theta::Vector{Float64}, H::Matrix{Float64})
    T = size(Y, 1)
    weights = zeros(T)
    H_inv = inv(H)
    for t in 1:T
        u = Y[t, :] - theta
        weights[t] = exp(-0.5 * dot(u, H_inv * u))
    end
    sum_w = sum(weights)
    if sum_w > 0
        weights ./= sum_w
    else
        weights .= 1.0 / T
    end
    return weights
end

"""
Effective Sample Size
"""
function effective_sample_size(weights::Vector{Float64})
    return 1.0 / sum(weights.^2)
end

"""
Empirical CVaR
"""
function empirical_cvar(w::Vector{Float64}, X::Matrix{Float64}, p::Vector{Float64}, tau::Float64)
    # X is T x N returns matrix
    T = size(X, 1)
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 5.0)
    
    @variable(model, z)
    @variable(model, u[1:T] >= 0)
    
    @objective(model, Min, z + (1.0/tau) * sum(p[t] * u[t] for t in 1:T))
    
    for t in 1:T
        @constraint(model, u[t] >= -dot(X[t, :], w) - z)
    end
    
    optimize!(model)
    return objective_value(model)
end

"""
Solve Nominal CVaR
"""
function solve_nominal_cvar(X::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    p = fill(1.0/T, T)
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 5.0)
    set_attribute(model, "time_limit", 10.0)
    
    @variable(model, 0 <= w[1:N] <= max_weight)
    @variable(model, z)
    @variable(model, u[1:T] >= 0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= target_return)
    
    for t in 1:T
        @constraint(model, u[t] >= -dot(X[t, :], w) - z)
    end
    
    @objective(model, Min, z + (1.0/tau) * sum(p[t] * u[t] for t in 1:T))
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL
        return value.(w), objective_value(model)
    else
        return fill(1.0/N, N), Inf
    end
end

"""
Solve Finite Regime CVaR (Benchmark)
"""
function solve_finite_regime_cvar(X::Matrix{Float64}, P_matrix::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    K = size(P_matrix, 1) # K regimes
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 5.0)
    
    @variable(model, t_var)
    @variable(model, 0 <= w[1:N] <= max_weight)
    @variable(model, z[1:K])
    @variable(model, u[1:K, 1:T] >= 0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= target_return)
    
    for k in 1:K
        @constraint(model, z[k] + (1.0/tau) * sum(P_matrix[k, i] * u[k, i] for i in 1:T) <= t_var)
        for i in 1:T
            @constraint(model, u[k, i] >= -dot(X[i, :], w) - z[k])
        end
    end
    
    @objective(model, Min, t_var)
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL
        return value.(w), value(t_var)
    else
        return fill(1.0/N, N), Inf
    end
end

"""
Minimum Variance
"""
function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0)
    N = size(cov_mat, 1)
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 5.0)
    
    @variable(model, 0 <= w[1:N] <= max_weight)
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= target_return)
    
    # Reformulate quadratic objective for HiGHS if using it, or use Ipopt
    # We will just write the QCP form, HiGHS supports QP
    @objective(model, Min, dot(w, cov_mat * w))
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL
        return value.(w)
    else
        return fill(1.0/N, N)
    end
end

"""
Master LP for Robust CVaR
"""
function solve_master_cvar(X::Matrix{Float64}, Y::Matrix{Float64}, active_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    K = length(active_thetas)
    
    P_matrix = zeros(K, T)
    for k in 1:K
        P_matrix[k, :] = get_kernel_weights(Y, active_thetas[k], H)
    end
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 5.0)
    
    @variable(model, t_var)
    @variable(model, 0 <= w[1:N] <= max_weight)
    @variable(model, z[1:K])
    @variable(model, u[1:K, 1:T] >= 0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= target_return)
    
    for k in 1:K
        @constraint(model, z[k] + (1.0/tau) * sum(P_matrix[k, i] * u[k, i] for i in 1:T) <= t_var)
        for i in 1:T
            @constraint(model, u[k, i] >= -dot(X[i, :], w) - z[k])
        end
    end
    
    @objective(model, Min, t_var)
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL
        return value.(w), value(t_var)
    else
        return fill(1.0/N, N), Inf
    end
end

"""
Continuous-State Oracle (Grid-Based Search)
For 2D state space, a fine grid is practically equivalent and very fast in Julia.
"""
function solve_oracle(w::Vector{Float64}, X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, tau::Float64)
    T = size(X, 1)
    max_cvar = -Inf
    best_theta = grid_thetas[1]
    
    # Pre-compute portfolio returns
    port_rets = zeros(T)
    for i in 1:T
        port_rets[i] = dot(X[i, :], w)
    end
    
    for theta in grid_thetas
        p = get_kernel_weights(Y, theta, H)
        
        # Sort to compute CVaR efficiently without LP
        # Or just use the LP, but manual sort is much faster
        # CVaR formulation: min_z z + 1/tau * sum p_t [-r_t - z]_+
        # Actually, since it's just one portfolio w, we can compute empirical CVaR directly:
        
        # Sort returns
        idx = sortperm(port_rets)
        sorted_rets = port_rets[idx]
        sorted_p = p[idx]
        
        cum_p = 0.0
        cvar_val = 0.0
        for i in 1:T
            if cum_p + sorted_p[i] < tau
                cvar_val += sorted_p[i] * sorted_rets[i]
                cum_p += sorted_p[i]
            else
                rem_p = tau - cum_p
                cvar_val += rem_p * sorted_rets[i]
                break
            end
        end
        cvar_val = -cvar_val / tau
        
        if cvar_val > max_cvar
            max_cvar = cvar_val
            best_theta = theta
        end
    end
    
    return best_theta, max_cvar
end

"""
Adaptive SIP Exchange Algorithm
"""
function solve_robust_sip(X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64; max_iter=20, tol=1e-4, max_weight=1.0)
    # Start with a single active state (e.g., the center of the grid or the most dense one)
    active_thetas = [grid_thetas[div(length(grid_thetas), 2)]]
    
    w_best = fill(1.0/size(X, 2), size(X, 2))
    lb = -Inf
    ub = Inf
    
    for iter in 1:max_iter
        w, lb_new = solve_master_cvar(X, Y, active_thetas, H, mu, tau, target_return, max_weight)
        
        if lb_new == Inf
            # Infeasible master
            break
        end
        w_best = w
        lb = lb_new
        
        best_theta, ub_new = solve_oracle(w_best, X, Y, grid_thetas, H, tau)
        ub = ub_new
        
        gap = ub - lb
        if gap <= tol
            break
        end
        
        push!(active_thetas, best_theta)
    end
    
    return w_best, lb, ub, active_thetas
end

end # module
