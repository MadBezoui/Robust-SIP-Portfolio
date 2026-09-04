module RobustSIP

using JuMP
using HiGHS
using LinearAlgebra
using Statistics
using Distributions

export get_kernel_weights, effective_sample_size, empirical_cvar, grad_cvar_theta, lipschitz_certificate, verify_continuous_cvar, solve_master_cvar_regularized, filter_grid_to_hull,
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
    has_primal = has_values(model)
    is_optimal = termination_status(model) == MOI.OPTIMAL
    if has_primal && !any(isnan.(value.(w)))
        return (
            weights = value.(w),
            objective = objective_value(model),
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = true,
            is_optimal = is_optimal,
            objective_bound = try objective_bound(model) catch; missing end,
            absolute_gap = try relative_gap(model) * abs(objective_value(model)) catch; missing end,
            relative_gap = try relative_gap(model) catch; missing end,
            target_req = target_return,
            target_impl = t_ret
        )
    else
        return (
            weights = fill(missing, N),
            objective = missing,
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = false,
            is_optimal = false,
            objective_bound = missing,
            absolute_gap = missing,
            relative_gap = missing,
            target_req = target_return,
            target_impl = t_ret
        )
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
    has_primal = has_values(model)
    is_optimal = termination_status(model) == MOI.OPTIMAL
    if has_primal && !any(isnan.(value.(w)))
        return (
            weights = value.(w),
            objective = value(t_var),
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = true,
            is_optimal = is_optimal,
            objective_bound = try objective_bound(model) catch; missing end,
            absolute_gap = try relative_gap(model) * abs(objective_value(model)) catch; missing end,
            relative_gap = try relative_gap(model) catch; missing end,
            target_req = target_return,
            target_impl = t_ret
        )
    else
        return (
            weights = fill(missing, N),
            objective = missing,
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = false,
            is_optimal = false,
            objective_bound = missing,
            absolute_gap = missing,
            relative_gap = missing,
            target_req = target_return,
            target_impl = t_ret
        )
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
    has_primal = has_values(model)
    is_optimal = termination_status(model) == MOI.OPTIMAL
    if has_primal && !any(isnan.(value.(w)))
        return (
            weights = value.(w),
            objective = objective_value(model),
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = true,
            is_optimal = is_optimal,
            objective_bound = try objective_bound(model) catch; missing end,
            target_req = target_return,
            target_impl = t_ret,
            gmv_fallback_used = false
        )
    else
        return (
            weights = fill(missing, N),
            objective = missing,
            termination_status = termination_status(model),
            primal_status = primal_status(model),
            dual_status = dual_status(model),
            has_primal = false,
            is_optimal = false,
            objective_bound = missing,
            target_req = target_return,
            target_impl = t_ret,
            gmv_fallback_used = false
        )
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
    
    has_primal = has_values(model)
    term_status = termination_status(model)
    prim_status = primal_status(model)
    du_status = dual_status(model)
    
    obj_val = has_primal ? objective_value(model) : missing
    obj_bound = missing
    try
        obj_bound = objective_bound(model)
    catch
    end
    abs_gap = (obj_val !== missing && obj_bound !== missing) ? abs(obj_val - obj_bound) : missing
    rel_gap = (obj_val !== missing && obj_bound !== missing && obj_val != 0) ? abs_gap / abs(obj_val) : missing
    
    diag = (
        Termination_Status = string(term_status),
        Primal_Status = string(prim_status),
        Dual_Status = string(du_status),
        Has_Primal_Solution = has_primal,
        Objective_Value = obj_val,
        Objective_Bound = obj_bound,
        Absolute_Gap = abs_gap,
        Relative_Gap = rel_gap
    )
    
    if term_status == MOI.OPTIMAL || term_status == MOI.LOCALLY_SOLVED || (term_status == MOI.TIME_LIMIT && has_primal)
        return value.(w), obj_val, diag
    else
        return missing, missing, diag
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
    mu_max = max_feasible_return(mu, max_weight)
    mu_min = min_feasible_return(mu, max_weight)
    impl_target = clamp(target_return, mu_min, mu_max - 1e-6)
    
    clamping_ind = (target_return != impl_target)
    adj_amount = impl_target - target_return
    
    clamping_audit = (
        req_target = target_return,
        impl_target = impl_target,
        mu_min = mu_min,
        mu_max = mu_max,
        clamp_ind = clamping_ind,
        adj = adj_amount
    )
    
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
    
    stop_reason = "ITERATION_LIMIT"
    final_gap = Inf
    last_status = (term_status="NOT_STARTED", primal_status="UNKNOWN")
    
    for iter in 1:max_iter
        w, lb_new, status = solve_master_cvar(X, Y, active_thetas, H, mu, tau, target_return, max_weight)
        w_best = w
        lb = lb_new
        last_status = status
        
        # If no valid primal solution from master LP, break early
        if ismissing(w_best)
            stop_reason = "FAILED_MASTER"
            break
        end
        
        best_theta, ub_new = solve_oracle(w_best, X, Y, grid_thetas, H, tau)
        ub = ub_new
        
        gap = ub - lb
        final_gap = gap
        push!(history, (iteration=iter, lb=lb, ub=ub, gap=gap, active_count=length(active_thetas), worst_theta=copy(best_theta)))
        
        # Convergence check: grid-restricted residual <= tol
        if gap <= tol
            stop_reason = "CONVERGED_TOLERANCE"
            break
        end
        
        # Avoid duplicate states
        if any(norm(best_theta - th) <= 1e-4 for th in active_thetas)
            stop_reason = "FAILED_DUPLICATE_WITH_POSITIVE_GAP"
            break
        end
        
        push!(active_thetas, copy(best_theta))
    end
    
    return w_best, lb, ub, active_thetas, history, last_status, final_gap, stop_reason, clamping_audit
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


# --- Phase M1: Continuous-Optimality Certification ---

"""
Analytic gradient of the conditional CVaR w.r.t state theta.
∇_θ Φ_τ(w,θ) = (1/τ) ∑_t ∇_θ p_t(θ) [l_t(w) - z^*(θ)]_+
"""
function grad_cvar_theta(w::Vector{Float64}, theta::Vector{Float64}, X::Matrix{Float64}, Y::Matrix{Float64}, H::Matrix{Float64}, tau::Float64)
    T = size(X, 1)
    H_inv = inv(H)
    
    # 1. Compute kernel weights
    log_w = zeros(T)
    for t in 1:T
        u = Y[t, :] - theta
        log_w[t] = -0.5 * dot(u, H_inv * u)
    end
    max_log = maximum(log_w)
    W = exp.(log_w .- max_log)
    P = W ./ sum(W)
    
    # 2. Compute y_bar
    y_bar = zeros(2)
    for t in 1:T
        y_bar += P[t] * Y[t, :]
    end
    
    # 3. Compute gradients of weights ∇_θ p_t(θ)
    grad_p = zeros(2, T)
    for t in 1:T
        grad_p[:, t] = P[t] .* (H_inv * (Y[t, :] - y_bar))
    end
    
    # 4. Compute losses and sort to find VaR z^*(θ)
    losses = -(X * w)
    idx = sortperm(losses, rev=true)
    sorted_losses = losses[idx]
    sorted_P = P[idx]
    
    cum_p = 0.0
    z_star = 0.0
    for i in 1:T
        cum_p += sorted_P[i]
        if cum_p >= tau
            z_star = sorted_losses[i]
            break
        end
    end
    
    # 5. Compute CVaR gradient
    grad_phi = zeros(2)
    for t in 1:T
        l_t = losses[t]
        if l_t > z_star
            grad_phi += grad_p[:, t] .* (l_t - z_star)
        end
    end
    
    return (1.0 / tau) .* grad_phi
end

"""
A priori Lipschitz Certificate L_Phi <= (4 * R * M_L) / (tau * lambda_min(H))
"""
function lipschitz_certificate(X::Matrix{Float64}, Y::Matrix{Float64}, H::Matrix{Float64}, tau::Float64, thetas::Vector{Vector{Float64}})
    T, N = size(X)
    
    # M_L = max_w max_t |X_t w| = max_t max_j |X_tj| (since w in simplex)
    M_L = maximum(abs.(X))
    
    # R = max_{t, θ} || Y_t - θ ||
    R = 0.0
    for t in 1:T
        for th in thetas
            d = norm(Y[t, :] - th)
            if d > R
                R = d
            end
        end
    end
    
    eigvals_H = eigen(H).values
    lambda_min_H = minimum(eigvals_H)
    
    L_Phi = (4.0 * R * M_L) / (tau * lambda_min_H)
    return L_Phi
end

"""
Projected gradient ascent over θ for A Posteriori Verification.
Starts from the best grid points and climbs the continuous CVaR surface.
"""
function verify_continuous_cvar(w::Vector{Float64}, X::Matrix{Float64}, Y::Matrix{Float64}, H::Matrix{Float64}, tau::Float64, top_thetas::Vector{Vector{Float64}}, bounds_v::Tuple{Float64,Float64}, bounds_d::Tuple{Float64,Float64}; max_steps=100, lr=1e-3)
    best_cvar = -Inf
    best_theta = top_thetas[1]
    
    for th_start in top_thetas
        th = copy(th_start)
        for step in 1:max_steps
            g = grad_cvar_theta(w, th, X, Y, H, tau)
            
            # Gradient ascent step
            th += lr .* g
            
            # Project onto box U
            th[1] = clamp(th[1], bounds_v[1], bounds_v[2])
            th[2] = clamp(th[2], bounds_d[1], bounds_d[2])
            
            # If gradient is tiny, break
            if norm(g) < 1e-6
                break
            end
        end
        
        # Evaluate final continuous CVaR
        _, val = solve_oracle(w, X, Y, [th], H, tau)
        if val > best_cvar
            best_cvar = val
            best_theta = copy(th)
        end
    end
    
    return best_theta, best_cvar
end


# --- Phase M2: Turnover Regularization ---

"""
Master LP augmented with L1 Turnover Regularization: lambda ||w - w_prev||_1
"""
function solve_master_cvar_regularized(X::Matrix{Float64}, Y::Matrix{Float64}, active_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64, w_prev::Union{Vector{Float64}, Nothing}, lambda_turnover::Float64)
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
    
    # Turnover penalty
    if w_prev !== nothing && lambda_turnover > 0.0
        @variable(model, turn_abs[1:N] >= 0.0)
        for j in 1:N
            @constraint(model, turn_abs[j] >= w[j] - w_prev[j])
            @constraint(model, turn_abs[j] >= w_prev[j] - w[j])
        end
        @objective(model, Min, t_var + lambda_turnover * sum(turn_abs))
    else
        @objective(model, Min, t_var)
    end
    
    optimize!(model)
    
    term_status = termination_status(model)
    if term_status == MOI.OPTIMAL || term_status == MOI.LOCALLY_SOLVED || (term_status == MOI.TIME_LIMIT && has_values(model))
        return value.(w), objective_value(model), term_status
    else
        return missing, missing, term_status
    end
end


# --- Phase M5: Convex Hull Geometry ---

"""
Filters a Cartesian grid to only include points inside the 2D convex hull of the observed data.
"""
function filter_grid_to_hull(grid::Vector{Vector{Float64}}, Y_obs::Matrix{Float64})
    # For a point p to be inside the convex hull of Y_obs,
    # it must be representable as a convex combination of points in Y_obs.
    # We can solve a small LP for each point to check membership, or use a package.
    # Since we want to keep dependencies low, we solve an LP for membership.
    
    T = size(Y_obs, 1)
    filtered_grid = Vector{Vector{Float64}}()
    
    for pt in grid
        model = Model(HiGHS.Optimizer)
        set_silent(model)
        @variable(model, lambda_vars[1:T] >= 0.0)
        @constraint(model, sum(lambda_vars) == 1.0)
        @constraint(model, Y_obs' * lambda_vars .== pt)
        @objective(model, Min, 0.0)
        optimize!(model)
        
        if termination_status(model) == MOI.OPTIMAL
            push!(filtered_grid, pt)
        end
    end
    return filtered_grid
end

end # module
