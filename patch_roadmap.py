import re
with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()
text = re.sub(
    r"The remainder of this paper is organized as follows.*?(?=\n\n)",
    "The remainder of this paper is organized as follows: Section 2 reviews related work. Section 3 defines the model. Section 4 establishes the theory. Section 5 presents the algorithms. Section 6 describes the experimental design. Section 7 details the main empirical results. Section 8 provides computational results. Section 9 explores model sensitivity. Section 10 offers discussion and conclusion.",
    text, flags=re.DOTALL
)
with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
