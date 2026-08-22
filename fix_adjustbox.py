import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Add packages
if "\\usepackage{adjustbox}" not in text:
    text = text.replace("\\usepackage{graphicx}", "\\usepackage{graphicx}\n\\usepackage{array}\n\\usepackage{tabularx}\n\\usepackage{makecell}\n\\usepackage{adjustbox}\n\\usepackage{microtype}")

# Replace \resizebox{\textwidth}{!}{ \begin{tabular}... \end{tabular} } with \begin{adjustbox}{max width=\textwidth} ... \end{adjustbox}
# It's easier to just do it manually for the tables, or use regex.
text = re.sub(r"\\resizebox\{\\textwidth\}\{!\}\{\s*(\\begin\{tabular\}.*?\\end\{tabular\})\s*\}", r"\\begin{adjustbox}{max width=\\textwidth}\n\1\n\\end{adjustbox}", text, flags=re.DOTALL)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
