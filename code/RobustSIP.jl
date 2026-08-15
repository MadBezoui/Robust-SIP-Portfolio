module RobustSIP

using JuMP
using HiGHS
using LinearAlgebra
using Statistics
using Distributions

export get_kernel_weights, effective_sample_size, empirical_cvar,
       max_feasible_return, min_feasible_return,
       solve_master_cvar, solve_oracle, solve_robust_sip,
       solve_nominal_cvar, solve_min_variance, solve_finite_regime_cvar,
       compute_dispersion_certificate

"""
Calculate maximum achievable expected return on the capped simplex:
  max mu' * w  s.t. sum(w) = 1, 0 <= w_i <= max_weight
For max_weight = c:
  q = floor(1/c), r = 1 - q*c
  mu_max = c * sum(mu_(1:q)) + r * mu_(q+1)
"""
function max_feasible_return(mu::Vector{Float64}, max_weight::Float64=1.0)
    N = length(mu)
    if max_weight >= 1.0
        return maximum(mu)
    end
    @assert N * max_weight >= 1.0 "Capped simplex is empty: N * max_weight < 1"
    
    sorted_mu = sort(mu, rev=true)
    q = floor(Int, 1.0 / max_weight)
    r = 1.0 - q * max_weight
    
    val = max_weight * sum(sorted_mu[1:q])
    if r > 1e-12 && q + 1 <= N
        val += r * sorted_mu[q + 1]
    end
    return val
end

"""
Calculate minimum achievable expected return on the capped simplex.
"""
function min_feasible_return(mu::Vector{Float64}, max_weight::Float64=1.0)
    N = length(mu)
    if max_weight >= 1.0
        return minimum(mu)
    end
    @assert N * max_weight >= 1.0 "Capped simplex is empty: N * max_weight < 1"
    
    sorted_mu = sort(mu) # ascending
    q = floor(Int, 1.0 / max_weight)
    r = 1.0 - q * max_weight
    
    val = max_weight * sum(sorted_mu[1:q])
    if r > 1e-12 && q + 1 <= N
        val += r * sorted_mu[q + 1]
    end
    return val
end

"""
Numerically stable log-sum-exp multivariate Gaussian Kernel Weights.
p_t(theta) = K_H(y_t - theta) / sum_s K_H(y_s - theta)
"""
function get_kernel_weights(Y::Matrix{Float64}, theta::Vector{Float64}, H::Matrix{Float64})
    T = size(Y, 1)
    H_inv = inv(H)
    logw = zeros(T)
    for t in 1:T
        u = Y[t, :] - theta
        logw[t] = -0.5 * dot(u, H_inv * u)
    end
    m = maximum(logw)
    w = exp.(logw .- m)
    sum_w = sum(w)
    if sum_w > 0.0
        w ./= sum_w
    else
        w .= 1.0 / T
    end
    return w
end

"""
Effective Sample Size (Kish's ESS) = 1 / sum(p_t^2)
"""
function effective_sample_size(weights::Vector{Float64})
    s = sum(weights.^2)
    return s > 0.0 ? (1.0 / s) : 1.0
end

"""
Empirical CVaR of portfolio loss -X * w under probabilities p at tail level tau.
Evaluated via fast sorting in O(T log T).
"""
function empirical_cvar(w::Vector{Float64}, X::Matrix{Float64}, p::Vector{Float64}, tau::Float64)
    T = size(X, 1)
    losses = -(X * w) # Loss = -return
    idx = sortperm(losses, rev=true) # Sorted descending losses (worst losses first)
    
    cum_p = 0.0
    cvar_val = 0.0
    for i in 1:T
        p_val = p[idx[i]]
        if cum_p + p_val <= tau
            cvar_val += p_val * losses[idx[i]]
            cum_p += p_val
        else
            rem_p = tau - cum_p
            cvar_val += rem_p * losses[idx[i]]
            cum_p += rem_p
            break
        end
    end
    return cvar_val / tau
end

"""
Solve Nominal (Unconditional) CVaR Portfolio
"""
function solve_nominal_cvar(X::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    p = fill(1.0/T, T)
    
    # Compute strictly feasible target return under capped simplex
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    t_ret = clamp(target_return, mu_min, mu_max - 1e-6)
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 600.0)
    
    @variable(model, 0.0 <= w[1:N] <= max_weight)
    @variable(model, z)
    @variable(model, u[1:T] >= 0.0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= t_ret)
    
    for t in 1:T
        @constraint(model, u[t] >= -dot(X[t, :], w) - z)
    end
    
    @objective(model, Min, z + (1.0/tau) * sum(p[t] * u[t] for t in 1:T))
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL || termination_status(model) == MOI.LOCALLY_SOLVED
        return value.(w), objective_value(model)
    else
        @warn "Nominal CVaR optimization did not reach optimal status ($(termination_status(model))). Returning equal weights."
        return fill(1.0/N, N), NaN
    end
end

"""
Solve Finite Regime CVaR (4-quadrant benchmark)
"""
function solve_finite_regime_cvar(X::Matrix{Float64}, P_matrix::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    K = size(P_matrix, 1) # K regimes
    
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    t_ret = clamp(target_return, mu_min, mu_max - 1e-6)
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 600.0)
    
    @variable(model, t_var)
    @variable(model, 0.0 <= w[1:N] <= max_weight)
    @variable(model, z[1:K])
    @variable(model, u[1:K, 1:T] >= 0.0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= t_ret)
    
    for k in 1:K
        @constraint(model, z[k] + (1.0/tau) * sum(P_matrix[k, i] * u[k, i] for i in 1:T) <= t_var)
        for i in 1:T
            @constraint(model, u[k, i] >= -dot(X[i, :], w) - z[k])
        end
    end
    
    @objective(model, Min, t_var)
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL || termination_status(model) == MOI.LOCALLY_SOLVED
        return value.(w), value(t_var)
    else
        @warn "Finite-regime CVaR optimization did not reach optimal status ($(termination_status(model))). Returning equal weights."
        return fill(1.0/N, N), NaN
    end
end

"""
Solve Target-Constrained Minimum Variance with Weight Cap and PSD Ridge
"""
function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0)
    N = size(cov_mat, 1)
    cov_psd = cov_mat + 1e-5 * Matrix(I, N, N) # Numerical PSD regularization
    
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    t_ret = clamp(target_return, mu_min, mu_max - 1e-6)
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 600.0)
    
    @variable(model, 0.0 <= w[1:N] <= max_weight)
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= t_ret)
    @objective(model, Min, dot(w, cov_psd * w))
    
    optimize!(model)
    if (termination_status(model) == MOI.OPTIMAL || has_values(model)) && !any(isnan.(value.(w)))
        return value.(w)
    else
        # Fallback to Global Minimum Variance (without target constraint)
        model_gmv = Model(HiGHS.Optimizer)
        set_silent(model_gmv)
        @variable(model_gmv, 0.0 <= w2[1:N] <= max_weight)
        @constraint(model_gmv, sum(w2) == 1.0)
        @objective(model_gmv, Min, dot(w2, cov_psd * w2))
        optimize!(model_gmv)
        if (termination_status(model_gmv) == MOI.OPTIMAL || has_values(model_gmv)) && !any(isnan.(value.(w2)))
            return value.(w2)
        else
            return fill(1.0/N, N)
        end
    end
end

"""
Master LP for Robust CVaR over active subset of states U_k
"""
function solve_master_cvar(X::Matrix{Float64}, Y::Matrix{Float64}, active_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)
    T, N = size(X)
    K = length(active_thetas)
    
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    t_ret = clamp(target_return, mu_min, mu_max - 1e-6)
    
    P_matrix = zeros(K, T)
    for k in 1:K
        P_matrix[k, :] = get_kernel_weights(Y, active_thetas[k], H)
    end
    
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    set_attribute(model, "time_limit", 600.0)
    
    @variable(model, t_var)
    @variable(model, 0.0 <= w[1:N] <= max_weight)
    @variable(model, z[1:K])
    @variable(model, u[1:K, 1:T] >= 0.0)
    
    @constraint(model, sum(w) == 1.0)
    @constraint(model, dot(mu, w) >= t_ret)
    
    for k in 1:K
        @constraint(model, z[k] + (1.0/tau) * sum(P_matrix[k, i] * u[k, i] for i in 1:T) <= t_var)
        for i in 1:T
            @constraint(model, u[k, i] >= -dot(X[i, :], w) - z[k])
        end
    end
    
    @objective(model, Min, t_var)
    
    optimize!(model)
    if termination_status(model) == MOI.OPTIMAL || termination_status(model) == MOI.LOCALLY_SOLVED || (termination_status(model) == MOI.TIME_LIMIT && has_values(model))
        if termination_status(model) == MOI.TIME_LIMIT
            @warn "Master CVaR LP reached TIME_LIMIT but has primal values. Using sub-optimal solution."
        end
        return value.(w), value(t_var), termination_status(model)
    else
        @warn "Master CVaR LP did not reach optimal status ($(termination_status(model)))"
        return fill(1.0/N, N), NaN, termination_status(model)
    end
end

"""
Grid-Based Separation Oracle
Evaluates worst-case conditional CVaR over discrete candidate grid \\widehat{U}.
Fully vectorized across all grid candidate states.
"""
function solve_oracle(w::Vector{Float64}, X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, tau::Float64)
    T = size(X, 1)
    K_states = length(grid_thetas)
    
    # Portfolio losses: l_t = -X_t * w
    port_losses = -(X * w)
    idx = sortperm(port_losses, rev=true) # descending losses
    sorted_losses = port_losses[idx]
    
    # Vectorized multivariate kernel weights for all grid points
    thetas_mat = hcat(grid_thetas...) # M x K_states
    H_inv = inv(H)
    
    # D_mat[t, k] = (Y_t - theta_k)' * H_inv * (Y_t - theta_k)
    # For diagonal or general H:
    log_w = zeros(T, K_states)
    for k in 1:K_states
        th = grid_thetas[k]
        for t in 1:T
            u1 = Y[t, 1] - th[1]
            u2 = Y[t, 2] - th[2]
            log_w[t, k] = -0.5 * (u1 * (H_inv[1, 1]*u1 + H_inv[1, 2]*u2) + u2 * (H_inv[2, 1]*u1 + H_inv[2, 2]*u2))
        end
    end
    
    max_log = maximum(log_w, dims=1)
    W = exp.(log_w .- max_log)
    P_all = W ./ sum(W, dims=1) # T x K_states
    
    sorted_P = P_all[idx, :] # T x K_states
    
    max_cvar = -Inf
    best_idx = 1
    
    for k in 1:K_states
        cum_p = 0.0
        cvar_val = 0.0
        for i in 1:T
            p_val = sorted_P[i, k]
            if cum_p + p_val <= tau
                cvar_val += p_val * sorted_losses[i]
                cum_p += p_val
            else
                rem_p = tau - cum_p
                cvar_val += rem_p * sorted_losses[i]
                cum_p += rem_p
                break
            end
        end
        cvar_val = cvar_val / tau
        
        if cvar_val > max_cvar
            max_cvar = cvar_val
            best_idx = k
        end
    end
    
    return grid_thetas[best_idx], max_cvar
end

"""
Adaptive Semi-Infinite Programming (SIP) Exchange Algorithm
Alternates between finite Master LP over active subset U_k and Separation Oracle over candidate grid \\widehat{U}.
"""
function solve_robust_sip(X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64; max_iter=15, tol=1e-4, max_weight=1.0)
    # Initialize active set with the nearest grid node to the most recent observed state
    y_T = collect(Y[end, :])
    best_dist = Inf
    nearest_theta = grid_thetas[1]
    for th in grid_thetas
        d = norm(th - y_T)
        if d < best_dist
            best_dist = d
            nearest_theta = copy(th)
        end
    end
    active_thetas = [nearest_theta]
    
    w_best = fill(1.0/size(X, 2), size(X, 2))
    lb = -Inf
    ub = Inf
    history = []
    
    last_status = nothing
    for iter in 1:max_iter
        w, lb_new, status = solve_master_cvar(X, Y, active_thetas, H, mu, tau, target_return, max_weight)
        w_best = w
        lb = lb_new
        last_status = status
        
        best_theta, ub_new = solve_oracle(w_best, X, Y, grid_thetas, H, tau)
        ub = ub_new
        
        gap = ub - lb
        push!(history, (iteration=iter, lb=lb, ub=ub, gap=gap, active_count=length(active_thetas), worst_theta=copy(best_theta)))
        
        # Convergence check: grid-restricted residual <= tol
        if gap <= tol
            break
        end
        
        # Avoid duplicate states
        if any(norm(best_theta - th) <= 1e-4 for th in active_thetas)
            break
        end
        
        push!(active_thetas, copy(best_theta))
    end
    
    return w_best, lb, ub, active_thetas, history, last_status
end

"""
Compute spatial dispersion radius rho and conservative Lipschitz bound certificate L_Phi * rho.
For state domain [v_min, v_max] x [d_min, d_max] with grid length n_v x n_d:
  delta_v = (v_max - v_min) / (n_v - 1)
  delta_d = (d_max - d_min) / (n_d - 1)
  rho = 0.5 * sqrt(delta_v^2 + delta_d^2)
"""
function compute_dispersion_certificate(v_range::Tuple{Float64, Float64}, d_range::Tuple{Float64, Float64}, n_v::Int, n_d::Int, H::Matrix{Float64}, X::Matrix{Float64}, tau::Float64)
    delta_v = (v_range[2] - v_range[1]) / (n_v - 1)
    delta_d = (d_range[2] - d_range[1]) / (n_d - 1)
    rho = 0.5 * sqrt(delta_v^2 + delta_d^2)
    
    # Conservative Lipschitz bound L_Phi on conditional CVaR w.r.t. state theta:
    # d/d_theta p_t(theta) = p_t(theta) * H^{-1} (y_t - theta - E_p[y - theta])
    # |d/d_theta Phi_tau(w, theta)| <= (1/tau) * max_t |loss_t| * ||H^{-1}|| * 2 * max_u ||u||
    # In daily return units, max loss <= 0.20, tau = 0.05 => (1/tau)*0.20 = 4.0
    # ||H^{-1}|| is spectral norm of inverse bandwidth matrix
    H_inv_norm = opnorm(inv(H), 2)
    domain_diam = sqrt((v_range[2] - v_range[1])^2 + (d_range[2] - d_range[1])^2)
    max_single_loss = maximum(abs.(X))
    
    L_Phi = (2.0 / tau) * max_single_loss * H_inv_norm * domain_diam
    certificate = L_Phi * rho
    
    return rho, L_Phi, certificate
end

end # module
