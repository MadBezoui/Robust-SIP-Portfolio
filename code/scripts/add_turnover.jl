content = read("src/RobustSIP.jl", String)

# solve_min_variance signature
old_min_var = "function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0; optimizer=HiGHS.Optimizer)"
new_min_var = "function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0, w_prev::Union{Vector{Float64}, Nothing}=nothing, turnover_limit::Float64=2.0; optimizer=HiGHS.Optimizer)"
content = replace(content, old_min_var => new_min_var)

# solve_min_variance constraint
old_w = "@constraint(model, sum(w) == 1.0)"
new_w = """@constraint(model, sum(w) == 1.0)
        if w_prev !== nothing
            @variable(model, d[1:N] >= 0)
            @constraint(model, w .- w_prev .<= d)
            @constraint(model, w_prev .- w .<= d)
            @constraint(model, sum(d) <= turnover_limit)
        end"""
content = replace(content, old_w => new_w)


# solve_master_cvar signature
old_mas = "function solve_master_cvar(X::Matrix{Float64}, Y::Matrix{Float64}, active_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0)"
new_mas = "function solve_master_cvar(X::Matrix{Float64}, Y::Matrix{Float64}, active_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64, max_weight::Float64=1.0, w_prev::Union{Vector{Float64}, Nothing}=nothing, turnover_limit::Float64=2.0)"
content = replace(content, old_mas => new_mas)
content = replace(content, old_w => new_w)

# solve_robust_sip signature
old_rob = "function solve_robust_sip(X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64; max_iter::Int=20, tol::Float64=1e-3, max_weight::Float64=1.0)"
new_rob = "function solve_robust_sip(X::Matrix{Float64}, Y::Matrix{Float64}, grid_thetas::Vector{Vector{Float64}}, H::Matrix{Float64}, mu::Vector{Float64}, tau::Float64, target_return::Float64; max_iter::Int=20, tol::Float64=1e-3, max_weight::Float64=1.0, w_prev::Union{Vector{Float64}, Nothing}=nothing, turnover_limit::Float64=2.0)"
content = replace(content, old_rob => new_rob)

# solve_robust_sip call to solve_master_cvar
old_call = "res = solve_master_cvar(X, Y, active_thetas, H, mu, tau, target_return, max_weight)"
new_call = "res = solve_master_cvar(X, Y, active_thetas, H, mu, tau, target_return, max_weight, w_prev, turnover_limit)"
content = replace(content, old_call => new_call)

write("src/RobustSIP.jl", content)
