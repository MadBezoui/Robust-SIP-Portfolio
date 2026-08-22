with open("code/gap_verification.jl", "r") as f:
    text = f.read()
import re
text = text.replace('"../data/aligned_market_data.csv"', 'joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")')
text = text.replace('"../results/gap_verification.csv"', 'joinpath(@__DIR__, "..", "results", "gap_verification.csv")')
text = text.replace('"data/aligned_market_data.csv"', 'joinpath(@__DIR__, "..", "data", "aligned_market_data.csv")')
text = text.replace('"results/gap_verification.csv"', 'joinpath(@__DIR__, "..", "results", "gap_verification.csv")')
with open("code/gap_verification.jl", "w") as f:
    f.write(text)
