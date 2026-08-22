with open("submission_CompOptAlg_v2/references.bib", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith("@article{politis1992circular"):
        skip = True
    if skip and line.strip() == "}":
        skip = False
        continue
    if not skip:
        new_lines.append(line)

with open("submission_CompOptAlg_v2/references.bib", "w") as f:
    f.writelines(new_lines)
