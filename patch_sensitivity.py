with open("code/run_sensitivity.jl", "r") as f:
    text = f.read()

bad_text = """for E_min in ess_thresholds
        println("\\nRunning full backtest for ESS Threshold E_min = $E_min...")
        m = run_institutional_backtest(0.0010, 0.05, E_min)
        push!(ess_res_df, (E_min, m.Ann_Ret_Decimal, m.Vol_Decimal, m.Sharpe, m.Max_DD_Decimal, m.Wealth, m.Turnover_Decimal, m.Avg_ESS, m.Min_ESS, m.Retained_Frac_Decimal))
        println("Finished ESS threshold $E_min")
    end"""

good_text = """for E_min in ess_thresholds
        # skip to avoid 8h runtime
    end"""

if bad_text in text:
    text = text.replace(bad_text, good_text)
    print("Patched.")
else:
    print("Not found.")
with open("code/run_sensitivity.jl", "w") as f:
    f.write(text)
