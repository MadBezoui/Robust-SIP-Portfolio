using Pkg; Pkg.activate(".")
include("RobustSIP.jl"); using .RobustSIP
include("main_exp.jl")

println("Starting Full Autoreview Backtest Tasks...")
# Let's run a subset (e.g. 20 windows) to demonstrate turnover regularization
println("Results will be saved to results/revision/")
