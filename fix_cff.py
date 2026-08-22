with open("CITATION.cff", "r") as f:
    text = f.read()

text = text.replace('    orcid: "https://orcid.org/0000-0000-0000-0000"\n', '')

# Also update version to 1.2.0
text = text.replace('version: 1.1.0', 'version: 1.2.0')

with open("CITATION.cff", "w") as f:
    f.write(text)
