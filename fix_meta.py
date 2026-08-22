with open("README.md", "r") as f:
    text = f.read()

import re
# Update README
text = re.sub(r"commit [a-f0-9]{7,40}", "commit 763899895767a0437dedeeb77536573af6b947c6", text)

with open("README.md", "w") as f:
    f.write(text)

with open("CITATION.cff", "r") as f:
    text = f.read()

text = re.sub(r"version: .*", "version: 1.4.0", text)
# add date-released, url etc.
text = re.sub(r"date-released: .*", "date-released: 2026-08-22", text)
if "url:" not in text:
    text += '\nurl: "https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.4.0-submission-final"\n'
else:
    text = re.sub(r"url: .*", 'url: "https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.4.0-submission-final"', text)

with open("CITATION.cff", "w") as f:
    f.write(text)
