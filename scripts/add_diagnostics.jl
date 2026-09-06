# Add diagnostics to RobustSIP.jl
file_path = "src/RobustSIP.jl"
content = read(file_path, String)

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
    # For 2D, we can use a simple LP or rely on bounds.
    # To keep dependencies light, we will use a quick LP:
    # min 0 s.t. Y' * lambda == y, sum(lambda) == 1, lambda >= 0
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

content = replace(content, "export get_kernel_weights" => "export get_kernel_weights, tail_specific_ess, is_in_convex_hull")
if !occursin("function tail_specific_ess", content)
    content = content * "\n" * diagnostics_code
end

write(file_path, content)
println("Diagnostics functions added to RobustSIP.jl")
