with open("code/03_statistical_inference.jl", "r") as f:
    text = f.read()

# Add `function run_statistical_inference()` at the top.
# But wait, there are using statements.
lines = text.split("\n")
imports = []
rest = []
for line in lines:
    if line.startswith("using "):
        imports.append(line)
    else:
        rest.append(line)

new_text = "\n".join(imports) + "\n\nfunction run_statistical_inference()\n" + "\n".join(rest) + "\nend\n"

with open("code/03_statistical_inference.jl", "w") as f:
    f.write(new_text)
