with open("submission_CompOptAlg_v2/references.bib", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("@article{bezanson2017julia") and len(new_lines) > 400:
        skip = True
    elif line.startswith("@article{dunning2017jump") and len(new_lines) > 400:
        skip = True
    
    if skip and line.strip() == "}":
        skip = False
        continue
    
    if not skip:
        new_lines.append(line)

with open("submission_CompOptAlg_v2/references.bib", "w") as f:
    f.writelines(new_lines)
