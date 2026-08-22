with open("README.md", "r") as f:
    text = f.read()

import re
old_section = re.search(r"## Release Information.*?(?=##|$)", text, re.DOTALL).group(0)

new_section = """## Release Information

The exact code and results corresponding to the manuscript are archived
under the GitHub release and annotated tag `v1.4.0-submission-final`,
corresponding to commit
`763899895767a0437dedeeb77536573af6b947c6`.

- Release:
  https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.4.0-submission-final
- Tag:
  https://github.com/MadBezoui/Robust-SIP-Portfolio/tree/v1.4.0-submission-final

"""
text = text.replace(old_section, new_section)
with open("README.md", "w") as f:
    f.write(text)
