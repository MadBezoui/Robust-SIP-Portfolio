import re

with open("src/RobustSIP.jl", "r") as f:
    code = f.read()

# Replace HiGHS.Optimizer with optimizer inside solve_min_variance only
# The function is defined as:
# function solve_min_variance(...; optimizer=HiGHS.Optimizer)
# ...
#    for scale in (1.0, 1.0e2)
#        model = Model(HiGHS.Optimizer)
#        set_silent(model)
#        set_attribute(model, "time_limit", 600.0)

pattern = r"(function solve_min_variance.*?\n.*?)(for scale in \(1\.0, 1\.0e2\)\s*\n\s*model = Model\()HiGHS\.Optimizer(\)\s*\n\s*set_silent\(model\)\s*\n\s*)set_attribute\(model, \"time_limit\", 600\.0\)"
replacement = r"\g<1>\g<2>optimizer\g<3>set_time_limit_sec(model, 60.0)"
code = re.sub(pattern, replacement, code, flags=re.DOTALL)

with open("src/RobustSIP.jl", "w") as f:
    f.write(code)
