content = read("src/RobustSIP.jl", String)

# 1. Add Clarabel and Exports
content = replace(content, "using HiGHS" => "using HiGHS\nusing Clarabel")
content = replace(content, "export get_kernel_weights" => "export get_kernel_weights, tail_specific_ess, is_in_convex_hull")

# 2. Modify solve_min_variance
old_min_var = "function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0)"
new_min_var = "function solve_min_variance(cov_mat::Matrix{Float64}, mu::Vector{Float64}, target_return::Float64, max_weight::Float64=1.0; optimizer=HiGHS.Optimizer)"
content = replace(content, old_min_var => new_min_var)

old_model = """        model = Model(HiGHS.Optimizer)
        set_silent(model)
        set_attribute(model, "time_limit", 600.0)"""
new_model = """        model = Model(optimizer)
        set_silent(model)
        if optimizer == HiGHS.Optimizer
            set_attribute(model, "time_limit", 600.0)
        end"""
content = replace(content, old_model => new_model)

# 3. Insert diagnostics before last 'end'
diagnostics_code = """
function tail_specific_ess(w::Vector{Float64}, X::Matrix{Float64}, p::Vector{Float64}, tau::Float64)
    losses = -(X * w)
    idx = sortperm(losses, rev=true)
    sorted_p = p[idx]
    
    cum_p = 0.0
    tail_weights = Float64[]
    for i in 1:length(p)
        if cum_p + sorted_p[i] <= tau
            push!(tail_weights, sorted_p[i] / tau)
            cum_p += sorted_p[i]
        else
            rem = tau - cum_p
            if rem > 0
                push!(tail_weights, rem / tau)
            end
            break
        end
    end
    return effective_sample_size(tail_weights)
end

function is_in_convex_hull(y::Vector{Float64}, Y::Matrix{Float64})
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    T = size(Y, 1)
    @variable(model, lambda[1:T] >= 0)
    @constraint(model, sum(lambda) == 1.0)
    @constraint(model, Y' * lambda .== y)
    optimize!(model)
    return termination_status(model) == MOI.OPTIMAL
end
"""

# Find last end
last_end_idx = findlast("end", content)
content = content[1:last_end_idx.start-1] * diagnostics_code * "\n" * content[last_end_idx.start:end]

write("src/RobustSIP.jl", content)
