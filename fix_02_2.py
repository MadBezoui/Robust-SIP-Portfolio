with open("code/02_evaluate_performance.jl", "r") as f:
    lines = f.readlines()
# The file has:
# if abspath(PROGRAM_FILE) == @__FILE__
#     evaluate_backtest(0.0010, 0.05)
# end
# end
# 
# if abspath(PROGRAM_FILE) == @__FILE__
#     evaluate_backtest(0.0010, 0.05)
# end
# Let's just remove everything after the first `end` that closes the function.
with open("code/02_evaluate_performance.jl", "w") as f:
    text = "".join(lines)
    # find the last function end and the guard
    idx = text.rfind("    println(\"Saved tc_sensitivity.csv\")\n    \n    # -------------------------------------------------------------------------")
    if idx != -1:
        text = text[:idx] + "    println(\"Saved tc_sensitivity.csv\")\nend\n\nif abspath(PROGRAM_FILE) == @__FILE__\n    evaluate_backtest(0.0010, 0.05)\nend\n"
    f.write(text)
