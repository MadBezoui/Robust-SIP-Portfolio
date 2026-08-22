with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

# Fix bar y(\theta)
text = text.replace(r"With $\bar{y}(\theta) = \sum_{s=1}^T p_s(\theta) y_{s-1}$.", "")

# Fix Proposition 1 programming syntax
# Search for the block starting with "Where the final term is omitted..."
# Let's just fix \mu_{\min}
bad_str = r"Where the final term is omitted when $r=0$. and $\mu_{\min} = \bar{w} \sum_{i=1}^q \hat{\mu}_{[i]} + (r > 0 ? r \hat{\mu}_{[q+1]} : 0)$, with the residual term omitted when $r=0$."
if bad_str in text:
    good_str = r"and $\mu_{\min} = \bar{w} \sum_{i=1}^q \hat{\mu}_{[i]} + \begin{cases} r \hat{\mu}_{[q+1]}, & r > 0 \\ 0, & r = 0 \end{cases}$."
    text = text.replace(bad_str, good_str)
else:
    print("Could not find the bad \mu_{\min} string")
    
# Let's also check \mu_{\max}
bad_str2 = r"and $\mu_{\max} = \dots" # wait, how is \mu_{\max} defined?
# Let's just run it to see.
with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
