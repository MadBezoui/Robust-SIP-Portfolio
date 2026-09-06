content = read("src/RobustSIP.jl", String)

# Fix solve_min_variance
old_smv = """    for scale in (1.0, 1.0e2)
        model = Model(HiGHS.Optimizer)
        set_silent(model)
        set_attribute(model, "time_limit", 600.0)"""

new_smv = """    for scale in (1.0, 1.0e2)
        model = Model(optimizer)
        set_silent(model)
        set_time_limit_sec(model, 60.0)"""
content = replace(content, old_smv => new_smv)

# Fix duplicate turnover constraint
dup_turnover = """if w_prev !== nothing
    @variable(model, d[1:N] >= 0)
    @constraint(model, w .- w_prev .<= d)
    @constraint(model, w_prev .- w .<= d)
    @constraint(model, sum(d) <= turnover_limit)
end
if w_prev !== nothing
    @variable(model, d[1:N] >= 0)
    @constraint(model, w .- w_prev .<= d)
    @constraint(model, w_prev .- w .<= d)
    @constraint(model, sum(d) <= turnover_limit)
end"""
single_turnover = """if w_prev !== nothing
    @variable(model, d[1:N] >= 0)
    @constraint(model, w .- w_prev .<= d)
    @constraint(model, w_prev .- w .<= d)
    @constraint(model, sum(d) <= turnover_limit)
end"""
content = replace(content, dup_turnover => single_turnover)

write("src/RobustSIP.jl", content)
