import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Fix Prop 1:
text = text.replace(
    r"Let $S_{\bar w}=\{w \in \mathbb{R}^N : \mathbf{1}^\top w=1,\ 0\leq w_i\leq\bar w\}$.",
    r"Let $S_{\bar w}=\{w \in \mathbb{R}^N : \mathbf{1}^\top w=1,\ 0\leq w_i\leq\bar w\}$ for a fixed upper bound $0 < \bar{w} \le 1$."
)

# Fix Prop 2:
text = text.replace(
    r"Assume that $H \succ 0$, $N\bar{w} \ge 1$, and $\mu_{\text{target}} \le \mu_{\max}$. Then:",
    r"Assume that $H \succ 0$, $N\bar{w} \ge 1$ with $0 < \bar{w} \le 1$, $\mu_{\text{target}} \le \mu_{\max}$, and $0 < \tau < 1$. Then:"
)

# Fix Prop 3 (Theorem 1 in earlier version):
text = text.replace(
    r"Assume that each master problem is solved to exact LP optimality and the separation oracle identifies the worst-case state $\theta^* = \arg\max_{\theta \in \mathcal{U}} \Phi_\tau(w^k, \theta)$ with exact value $G(w^k) = \Phi_\tau(w^k, \theta^*)$. Then:",
    r"Assume that $0 < \tau < 1$, each master problem is solved to exact LP optimality, and the separation oracle identifies the worst-case state $\theta^* = \arg\max_{\theta \in \mathcal{U}} \Phi_\tau(w^k, \theta)$ with exact value $G(w^k) = \Phi_\tau(w^k, \theta^*)$. Then:"
)

# Add Corollary for Finite Grid:
corollary = r"""
\begin{corollary}[Finite-grid termination]
For a finite candidate set $\widehat{\mathcal{U}}$, exact master solves and exact full-grid separation, the exchange algorithm terminates after at most $|\widehat{\mathcal{U}}|$ distinct state additions and returns an $\varepsilon$-optimal solution of the grid-restricted problem.
\end{corollary}
"""
text = text.replace(r"\end{proposition}", r"\end{proposition}" + corollary, 1) # wait, I want to add it after Proposition 3

# Wait, replacing the 3rd \end{proposition} is tricky. Let's just find the end of Prop 3.
prop3_end = r"\end{proposition}"
# Actually, the string "\end{proposition}" appears 3 times.
# We want to add the corollary right after the 3rd one.
parts = text.split(r"\end{proposition}")
if len(parts) == 4:
    text = parts[0] + r"\end{proposition}" + parts[1] + r"\end{proposition}" + parts[2] + r"\end{proposition}" + corollary + parts[3]

# 2.4 Clarify the Lipschitz expression
old_lip = r"L_\Phi := \frac{4 R M_L}{\tau \lambda_{\min}(H)}"
new_lip = r"L_\Phi = \frac{4 R M_L}{\tau \lambda_{\min}(H)}"
text = text.replace(old_lip, new_lip)
# also add "where the $L_2$ norm is used in $R$, $\rho$, and the gradient norm."
text = text.replace(
    r"where $R = \sup_{\theta, t}\|y_{t-1} - \theta\|$ is the maximum state distance and $M_L$ bounds the portfolio loss.",
    r"where $R = \sup_{\theta, t}\|y_{t-1} - \theta\|_2$ is the maximum state distance, $M_L$ bounds the portfolio loss, and the standard Euclidean norm $\|\cdot\|_2$ is used for $R$, the grid dispersion $\rho$, and the gradient norm."
)
# change \rho definition
text = text.replace(r"\| \theta - \hat{\theta} \|", r"\| \theta - \hat{\theta} \|_2")

# Display the fraction clearly:
text = text.replace(r"A direct evaluation of the conservative bound $\frac{4RM_L}{\tau\lambda_{\min}(H)}$", 
                    r"A direct evaluation of the conservative bound $L_\Phi$")

# Check 3.1: p-value formula
p_val_formula = r"""
The centered two-sided bootstrap $p$-value is defined as:
\begin{equation}
\widehat{p} = \frac{1+\sum_{b=1}^{B} \mathbf{1} \left\{ \left|\Delta \mathrm{SR}_b^\ast-\overline{\Delta \mathrm{SR}^\ast}\right| \ge |\widehat{\Delta \mathrm{SR}}| \right\}}{B+1}
\end{equation}
where $B=10000$ and a fixed seed (\texttt{20260814}) is utilized for exact reproducibility. The confidence interval is the percentile interval based on the empirical 2.5\% and 97.5\% quantiles.
"""
text = text.replace(r"to evaluate the statistical significance of out-of-sample Sharpe ratio differences $\Delta \mathrm{SR}$.", 
                    r"to evaluate the statistical significance of out-of-sample Sharpe ratio differences $\Delta \mathrm{SR}$. " + p_val_formula)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
print("Math issues addressed")
