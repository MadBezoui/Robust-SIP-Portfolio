import re
with open("code/generate_publication_figures.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "ax.set_title(" in line:
        indent = len(line) - len(line.lstrip())
        new_lines.append(" " * indent + "try:\n")
        new_lines.append(" " * (indent + 4) + "ax.set_xlim(dates.min(), dates.max())\n")
        new_lines.append(" " * indent + "except NameError:\n")
        new_lines.append(" " * (indent + 4) + "pass\n")
    new_lines.append(line)

with open("code/generate_publication_figures.py", "w") as f:
    f.writelines(new_lines)
