import re

with open("code/gap_verification.jl", "r") as f:
    text = f.read()

text = text.replace('"data/aligned_market_data.csv"', '"../data/aligned_market_data.csv"')
text = text.replace('"results/gap_verification.csv"', '"../results/gap_verification.csv"')

with open("code/gap_verification.jl", "w") as f:
    f.write(text)
