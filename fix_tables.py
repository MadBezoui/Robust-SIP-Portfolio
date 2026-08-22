with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Fix Table 4 TC-MinVar values
text = text.replace("TC-MinVar & 10.73\\% & 12.32\\% & 0.871", "TC-MinVar & 10.75\\% & 12.32\\% & 0.873")

# Fix Table 7 Adaptive exchange row
old_tab7 = """Adaptive exchange, $21\\times21$ grid & Exchange residual \\\\
$\\le 10^{-4}$ & 5 active state blocks & 4.49 s
& final grid-oracle value $\\approx 3.3562\\%$ \\\\"""
new_tab7 = """Adaptive exchange, $21\\times21$ grid & Exchange residual \\\\
$\\le 10^{-4}$ & 5 active state blocks & 4.49 s
& LB $\\approx 3.356246\\%$, oracle $\\approx 3.358510\\%$ \\\\"""
text = text.replace(old_tab7, new_tab7)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
print("Fixed tables.")
