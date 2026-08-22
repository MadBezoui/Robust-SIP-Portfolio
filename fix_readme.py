import re
with open("README.md", "r") as f:
    text = f.read()

# Replace commit hash instruction
text = re.sub(r"git checkout [0-9a-f]{7,40}", r"git checkout v1.4.0-submission-final", text)

# Replace the pipeline commands if main_exp is used
commands = """cd code
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. main_exp.jl"""

# find the bash block
text = re.sub(r"```bash\ncd code\njulia --project=\. main_exp\.jl\n```", f"```bash\n{commands}\n```", text)

with open("README.md", "w") as f:
    f.write(text)
