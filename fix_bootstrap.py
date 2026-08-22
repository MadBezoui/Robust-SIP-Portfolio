with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""\widehat p = \frac{1}{B}\sum_{b=1}^B \mathbf 1 \left\{ \left| \Delta\mathrm{SR}^{*b} - \overline{\Delta\mathrm{SR}^{*}} \right| \ge \left| \widehat{\Delta\mathrm{SR}} \right| \right\}.
\]"""

new_text = r"""\widehat p =
\frac{
1+\sum_{b=1}^{B}
\mathbf 1\!\left\{
\left|
\Delta\mathrm{SR}^{*b}
-\overline{\Delta\mathrm{SR}^{*}}
\right|
\ge
\left|
\widehat{\Delta\mathrm{SR}}
\right|
\right\}
}{B+1},
\qquad
\overline{\Delta\mathrm{SR}^{*}}
=
\frac1B\sum_{b=1}^{B}\Delta\mathrm{SR}^{*b}.
\]"""

text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
