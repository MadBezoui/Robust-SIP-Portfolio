import re

# Fix 01
with open("code/01_run_backtest.jl", "r") as f:
    text = f.read()
if "function run_backtest(" not in text:
    # Find where the actual script logic starts after includes/using
    idx = text.find("input_file = ")
    if idx != -1:
        text = text[:idx] + "function run_backtest()\n" + text[idx:] + "\nend\n\nif abspath(PROGRAM_FILE) == @__FILE__\n    run_backtest()\nend\n"
    with open("code/01_run_backtest.jl", "w") as f:
        f.write(text)

# Fix 03
with open("code/03_statistical_inference.jl", "r") as f:
    text = f.read()
if "function run_statistical_inference(" not in text:
    idx = text.find("perf_file = ")
    if idx != -1:
        text = text[:idx] + "function run_statistical_inference()\n" + text[idx:] + "\nend\n\nif abspath(PROGRAM_FILE) == @__FILE__\n    run_statistical_inference()\nend\n"
    with open("code/03_statistical_inference.jl", "w") as f:
        f.write(text)

