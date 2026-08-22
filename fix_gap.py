import re

with open("code/gap_verification.jl", "r") as f:
    text = f.read()

# 5.1 Wrong bandwidth: H = [(c * std_v)^2 0.0; 0.0 (c * std_d)^2]
text = text.replace("H = [(c * std_v)^2 0.0; 0.0 (c * std_d)^2]",
                    "H = T^(-1/3) * [(c * std_v)^2 0.0; 0.0 (c * std_d)^2]")

# 5.2 Wrong return target: target_return = max(minimum(mu_train), 0.001)
text = text.replace("target_return = max(minimum(mu_train), 0.001)",
                    "target_return = median(mu_train)")
text = text.replace("using JuMP, HiGHS, LinearAlgebra, CSV, DataFrames, Dates, Statistics", "using JuMP, HiGHS, LinearAlgebra, CSV, DataFrames, Dates, Statistics\nusing Base.Math")

# 5.3 State-domain mismatch: bounds_d = (d_min - d_margin, d_max + d_margin)
text = text.replace("bounds_d = (d_min - d_margin, d_max + d_margin)",
                    "bounds_d = (max(0.0, d_min - d_margin), min(1.0, d_max + d_margin))")

# 5.4 Date selection is imprecise: findfirst(...)
# Replace findfirst with a better date selection or just use the exact indices
# I will find the lines and replace them.
text = re.sub(r"idx\s*=\s*findfirst\(.*?, dates\)",
              r"idx = findlast(x -> x <= d, dates)", text)

with open("code/gap_verification.jl", "w") as f:
    f.write(text)
