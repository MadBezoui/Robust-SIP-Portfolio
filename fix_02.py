import re

with open("code/02_evaluate_performance.jl", "r") as f:
    text = f.read()

# Make sure it only has the evaluate_backtest definition and the guard.
# Actually I'll just remove the trailing execution if it's duplicated.
# Let's see what is inside 02_evaluate_performance.jl
