with open("README.md", "r") as f:
    text = f.read()

import re
text = text.replace("v1.4.0-submission-final", "v1.5.0-submission-final")
# wait, the commit hash won't be known until I commit!
# So I should commit first, get the hash, then update README!
