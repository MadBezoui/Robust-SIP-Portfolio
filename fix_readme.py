import re

with open("README.md", "r") as f:
    text = f.read()

text = text.replace("v1.1.0", "v1.2.0-submission-final")
text = re.sub(r"commit `[0-9a-f]+`", "commit `bd9c810`", text) # The commit hash of the tag I just created was bd9c810.

# Also update the figure count in README
text = text.replace("10 analytical PDF plots", "13 analytical PDF plots")

with open("README.md", "w") as f:
    f.write(text)
