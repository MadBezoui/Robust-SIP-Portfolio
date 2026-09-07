
Below is a **concrete revision plan** for the manuscript. I have written it as an action plan: **where to modify, what is wrong, what exactly to replace/add, and why**.

# Revision Plan for the Manuscript

## A. Mandatory corrections before resubmission

| Priority           | Where                            | What must be modified                             | Exact modification                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------ | -------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Critical** | Abstract, p. 1                   | Computational times are inconsistent with Table 7 | Replace**“from 441 to 5 state blocks and the solve time from 72.7 to 4.5 seconds”** with**“from 441 to 5 state blocks and the solve time from 71.43 to 3.45 seconds, corresponding to a 20.7× speedup on the representative benchmark instance.”** Table 7 reports 3.45 s versus 71.43 s.                                                                                                                                                         |
| **Critical** | Section 5.3–5.4, pp. 15–16     | Lipschitz constant numerical contradiction        | The manuscript first obtains\(L_\Phi\approx8\times10^5\), but subsequently says the same conservative bound is of order \(10^2\)–\(10^3\).   Recalculate the value window by window and retain **only one consistent magnitude**. With the numerical values currently written in Section 5.3, \(L_\Phi\) is approximately \(7.8\times10^5\), so the \(10^2\)–\(10^3\) statement should probably be removed unless it refers to a different quantity. |
| **Critical** | Table 4 vs. discussion of Fig. 8 | TC-MinVar turnover is inconsistent                | Table 4 gives**5.93%**, while the Fig. 8 discussion says **7.0%**.   Recompute from the code and use the same number everywhere.                                                                                                                                                                                                                                                                                                                 |
| **Critical** | Data Availability + Ref. [8]     | Two Zenodo DOIs are reported                      | Data Availability gives`10.5281/zenodo.22309074`, while Ref. [8] gives `10.5281/zenodo.21957758`.   If one is a version DOI and the other is a concept/archive DOI, state this explicitly. Otherwise retain only the DOI corresponding exactly to the submitted results.                                                                                                                                                                                 |
| **High**     | Section 8 / Conclusion           | Solver tolerance terminology                      | Clearly distinguish**LP solver feasibility/optimality tolerance \(10^{-8}\)** from **exchange termination tolerance \(10^{-4}\)**. Currently both appear and could be misread as contradictory.                                                                                                                                                                                                                                                  |

### Recommended replacement for the abstract computational sentence

Use:

> “For computation, we employ a grid-restricted separation oracle and solve the resulting finite approximation by adaptive constraint generation. On a representative benchmark instance, the method reduces the master problem from 441 state blocks to 5 active blocks and decreases wall-clock solution time from 71.43 s to 3.45 s, corresponding to a 20.7× speedup relative to the dense 21×21 extensive-form LP.”

This is fully consistent with Table 7.

---

# B. Strengthen the novelty statement in the Introduction

## Where

End of Section 1, around the current contribution paragraph.

The manuscript currently states that its contribution is methodological and empirical and describes the continuous-state robust model, theoretical properties, constraint generation, and long OOS experiment.

The problem is that the contribution is somewhat diffuse. A reviewer may see CVaR, kernel regression, SIP, and constraint generation as individually established techniques.

## Replace the existing contribution paragraph with a sharper three-part statement

Suggested text:

> **“This paper makes three contributions. First, we introduce a state-robust portfolio formulation in which robustness is imposed over a continuum of covariate-indexed kernel-weighted empirical conditional return distributions, rather than over a distributional ambiguity set or a finite collection of regimes. This construction produces a semi-infinite CVaR optimization problem in which a single allocation is protected against all admissible market states. Second, we establish well-posedness, continuity, convexity, and grid-approximation properties of the resulting formulation, and develop a grid-restricted exchange algorithm that exploits the small number of binding state constraints. Third, using a 31.5-year rolling out-of-sample experiment, we show that the method is computationally tractable and economically competitive in wealth terms, while not delivering statistically significant Sharpe-ratio improvements over simpler CVaR benchmarks. The empirical results therefore identify the principal benefit of continuous-state robustness as structural and stabilizing rather than as unconditional performance dominance.”**

This framing is much stronger because it does **not claim that exchange algorithms themselves are novel**.

---

# C. Add a new sensitivity analysis for the 10% state-domain expansion

## Why this is necessary

The uncertainty domain is currently expanded by a fixed **10% margin** beyond observed training-window extrema.

But the robustness operator takes a worst case over this domain. Therefore, 10% is not a minor technical setting; it directly determines what is considered an adverse state.

The current sensitivity section studies grid resolution, bandwidth, ESS threshold and bootstrap block size, but not this domain margin.

## What to add

Create a new subsection:

### **9.X Sensitivity to state-domain expansion**

Evaluate:

$$
\delta \in \{0\%,5\%,10\%,20\%\}.
$$

Report at least:

| Margin |   Return | Volatility |   Sharpe |   Max DD | Turnover | Mean ESS active states | Worst-case CVaR |
| -----: | -------: | ---------: | -------: | -------: | -------: | ---------------------: | --------------: |
|     0% |          |            |          |          |          |                        |                 |
|     5% |          |            |          |          |          |                        |                 |
|    10% | baseline |   baseline | baseline | baseline | baseline |               baseline |        baseline |
|    20% |          |            |          |          |          |                        |                 |

Also report where the worst-case state lies.

## Suggested text to add before the table

> “Because the state-domain margin directly controls the set of adverse market environments considered by the robust optimization problem, we assess the sensitivity of the results to the expansion parameter. Specifically, we repeat the complete rolling experiment for domain expansions of 0%, 5%, 10%, and 20% beyond the training-window extrema. This experiment distinguishes robustness attributable to the continuous-state formulation from robustness induced by the particular choice of domain size.”

This is one of the most important additions for a Q1 revision.

---

# D. Add a sensitivity analysis for the expected-return target

## Current problem

The target return is set to the cross-sectional median of historical asset means.

Yet the manuscript itself admits that the higher volatility and concentration of Robust SIP may come from the interaction of return targeting, state conditioning, and boundary effects.

This question is currently left unresolved.

## Add a new subsection

### **9.X Sensitivity to the expected-return constraint**

I recommend at least four specifications:

$$
\mu_{\text{target}} \in
\{
\text{none},
Q_{25}(\hat\mu),
Q_{50}(\hat\mu),
Q_{75}(\hat\mu)
\}.
$$

Or, if you want a simpler experiment:

* no expected-return constraint;
* 50% of baseline target;
* baseline target;
* 125% of baseline target, subject to feasibility.

## Main variables to report

* return;
* volatility;
* Sharpe;
* maximum drawdown;
* turnover;
* effective number of assets;
* binding states;
* worst-case conditional CVaR.

## Suggested conclusion to seek

Do **not** assume the result in advance. The purpose is to answer:

> “Is Robust SIP intrinsically more volatile, or is its realized volatility primarily generated by the return-target constraint?”

This experiment could substantially improve the paper.

---

# E. Strengthen the benchmark set

## Current benchmark weakness

The Finite-Regime CVaR benchmark uses only four regimes formed by independent median splits on log-VIX and drawdown.

A strong reviewer can argue that this is an intentionally simple discrete benchmark.

Also, the paper cites modern conditional portfolio / conditional DRO work but does not directly compare against such a method.

## What to add

Add **at least one stronger state-aware comparator**.

Best options, in order of value:

| Comparator                         | Why it helps                                       |
| ---------------------------------- | -------------------------------------------------- |
| Regularized state-conditioned CVaR | Closest to your framework and computationally easy |
| Conditional DRO                    | Strongest theoretical comparison                   |
| HMM/regime-switching CVaR          | Stronger discrete-regime benchmark                 |
| Shrinkage conditional CVaR         | Separates conditioning from robustness             |

A particularly practical comparator would be:

$$
\hat P_t^{(\lambda)}
=
(1-\lambda)\hat P
+
\lambda \hat P_{y_t},
$$

followed by nominal CVaR optimization.

Evaluate several \(\lambda\) values.

This would show whether your robust layer adds value relative to a **regularized conditional prescription**, rather than only relative to the very unstable pure state-conditioned strategy.

---

# F. Reframe the empirical message

This is a major improvement opportunity.

Currently, Robust SIP does **not** have the best Sharpe ratio:

* Finite-Regime CVaR: 0.901
* Nominal CVaR: 0.880
* TC-MinVar: 0.875
* Robust SIP: 0.809.

It also does not outperform the CVaR benchmarks during the principal crises.

Therefore, do not try to present the method primarily as a superior investment strategy.

Your strongest empirical finding is elsewhere:

**pure state conditioning is extremely unstable, whereas robustness across the state domain substantially regularizes the allocation.**

State-conditioned CVaR generates **35.74% turnover**, compared with **9.48% for Robust SIP**.

## Replace the current central empirical narrative with

> “The empirical value of the robust layer does not arise from unconditional dominance in risk-adjusted performance. Rather, robustness over the state domain acts as a regularization mechanism against excessive responsiveness to short-lived movements in the conditioning variables. Pure state-conditioned CVaR generates substantially higher turnover and lower terminal wealth, whereas the robust formulation stabilizes the allocation by requiring satisfactory tail-risk performance over an entire set of plausible market states.”

That is a much stronger and more defensible contribution.

---

# G. Improve the statistical analysis

## 1. Add a non-zero risk-free rate robustness test

The reported Sharpe ratios currently assume a zero risk-free rate.

For a 1994–2026 backtest, reviewers may challenge that assumption.

### Add

A supplementary table using monthly/daily Treasury-bill returns or another standard short-term risk-free proxy.

Report:

* original zero-rate Sharpe;
* excess-return Sharpe.

The ranking may remain the same, but showing this removes an easy reviewer objection.

---

## 2. Retain the bootstrap but soften the wording

The current bootstrap results are appropriate and show no significant Sharpe difference; for nominal CVaR:

$$
\Delta SR=-0.0713,\quad
CI=[-0.1990,0.0569],\quad
p=0.281.
$$

Use wording such as:

> “The block-bootstrap analysis provides no evidence that the observed Sharpe-ratio differences are statistically distinguishable from zero over the evaluation sample.”

Avoid formulations suggesting that the test “proves equality.”

---

# H. Clarify mathematical well-posedness versus statistical reliability

The Gaussian kernel guarantees strictly positive probabilities and therefore a mathematically well-defined conditional empirical distribution for every state.

But some active states have extremely weak support; the minimum window-level mean ESS is only **2.18**.

These are two different issues.

## Add the following paragraph at the end of Section 3.2

> “We emphasize that mathematical well-posedness and statistical reliability are distinct. The strict positivity of the Gaussian kernel ensures that \(\hat P_\theta\) is defined for every \(\theta\in U\), but it does not imply that every conditional distribution is estimated with comparable statistical precision. In low-support regions, the conditional empirical measure may effectively depend on only a small number of historical observations. We therefore use ESS as a diagnostic of local estimation reliability and explicitly study ESS-restricted state domains in Section 9.”

This sentence would significantly improve the conceptual precision of the paper.

---

# I. Improve the computational evidence

The average number of active states is only **3.66 out of 441**, which is an excellent result.

However, the main dense-LP speed comparison is based on a representative instance, and the manuscript itself admits that row generation on the dense grid could be more competitive.

## Add a scalability experiment

Suggested table:

| \(N\) | \(T\) |   Grid | Dense LP time | Exchange time | Speedup | Active states | Objective gap |
| ----: | ----: | -----: | ------------: | ------------: | ------: | ------------: | ------------: |
|    10 |   500 | 11×11 |               |               |         |               |               |
|    20 |  1000 | 21×21 |               |               |         |               |               |
|    30 |  1260 | 21×21 |               |               |         |               |               |
|    30 |  1260 | 41×41 |               |               |         |               |               |
|    30 |  1260 | 81×81 |               |               |         |               |               |

At minimum, vary **grid size** and **number of assets**.

Then rewrite the computational contribution as:

> “The principal computational advantage is not merely the reduction in one benchmark instance, but the empirical observation that the number of binding state constraints remains small as the candidate grid is refined.”

That is much stronger.

---

# J. Correct Figures 6 and 7

The text says Figures 6 and 7 “compare the dynamic allocation weights,” but the plotted variable is actually **Effective Number of Assets**.

## Option 1 — Recommended

Replace the figures with actual allocation heatmaps:

* x-axis: time;
* y-axis: 30 industries;
* value: portfolio weight.

One figure for Robust SIP and one for TC-MinVar.

Then retain the statement that the figures compare dynamic asset allocations.

## Option 2 — Minimal revision

Keep the current figures, but rename them:

* **Fig. 6. Effective number of assets in the Robust SIP portfolio over time**
* **Fig. 7. Effective number of assets in the TC-MinVar portfolio over time**

And replace:

> “Figures 6 and 7 compare the dynamic allocation weights…”

with:

> “Figures 6 and 7 compare the evolution of portfolio concentration, measured by the effective number of assets, for Robust SIP and TC-MinVar.”

---

# K. Add exact crisis-window dates to Table 5

Table 5 reports Dot-Com, GFC, COVID and Inflation results but not the exact start/end dates of those evaluation windows.

Modify the table to:

| Crisis | Start date | End date | Strategy | Return | Max DD |
| ------ | ---------- | -------- | -------- | -----: | -----: |

Then add one sentence:

> “Crisis intervals are defined ex ante using the dates reported in Table 5 and are applied identically to all strategies.”

This prevents accusations of ex-post window selection.

---

# L. Add robustness using an external market drawdown indicator

The current drawdown state is calculated using an equal-weighted composite of the same 30 industries used in the optimization.

This is defensible, but reviewers may ask whether the state variable is partly endogenous to the investment universe.

## Add one robustness experiment

Use an external broad-market proxy for drawdown.

Then report:

* performance;
* active states;
* ESS;
* correlation between the two drawdown indicators;
* allocation distance.

You do not necessarily need to change the baseline. You only need to show that the conclusions are not driven by the specific internally constructed drawdown proxy.

---

# M. Add one bandwidth-geometry robustness test

The current bandwidth matrix is diagonal even though the manuscript acknowledges correlation between log-VIX and drawdown.

You already test bandwidth scale, which is good, but not bandwidth orientation.

Add one comparison between:

$$
H_{\text{diag}}
$$

and

$$
H_{\text{full}}
=
T^{-1/3}\hat\Sigma_y.
$$

Report:

* worst-case CVaR;
* Sharpe;
* turnover;
* active states;
* mean ESS.

This would close another potential reviewer objection.

---

# N. Explain the mismatch between risk horizon and holding horizon

The optimization minimizes **daily CVaR**, while the portfolio is held for **21 trading days**. The backtest protocol clearly uses 21-day holding periods.

Add a paragraph in Section 6 explaining this choice.

Suggested text:

> “The optimization objective is based on one-day conditional returns, whereas portfolio weights are held for 21 trading days. This design is intentional: daily observations provide substantially greater effective sample size for estimating state-dependent tail distributions, while monthly rebalancing limits portfolio turnover. The model therefore uses high-frequency information for estimation but lower-frequency portfolio implementation.”

Even better: add a sensitivity with 5-day or 21-day aggregated returns if computationally feasible.

---

# O. Suggested revised conclusion

The conclusion is currently mostly correct, but it can be sharper.

I recommend replacing its central conclusion with:

> “The results do not establish that continuous-state robustification dominates nominal or finite-regime CVaR in risk-adjusted performance. Instead, the evidence supports a more specific conclusion. First, continuous state dependence can be incorporated into a convex robust portfolio model without requiring discrete regime boundaries. Second, despite the continuum of state-indexed constraints, the finite grid approximation is computationally sparse: only a small number of state blocks become active in the master problem. Third, robustness across the state domain substantially stabilizes the highly reactive allocations produced by pure state-conditioned CVaR. The principal contribution is therefore methodological and computational, with state robustness acting as a regularizing mechanism rather than as a guarantee of superior investment performance.”

This conclusion matches the evidence much better.

---

# Recommended order of work

|        Order | Action                                                                 | Importance                                   |
| -----------: | ---------------------------------------------------------------------- | -------------------------------------------- |
|  **1** | Correct computational times, Lipschitz values, turnover and Zenodo DOI | **Mandatory**                          |
|  **2** | Add domain-margin sensitivity                                          | **Mandatory for strong Q1 submission** |
|  **3** | Add return-target sensitivity                                          | **Mandatory for strong Q1 submission** |
|  **4** | Add one stronger conditional benchmark                                 | **Very high value**                    |
|  **5** | Reframe contribution around robustness as stabilization/regularization | **Very high value**                    |
|  **6** | Add non-zero risk-free Sharpe analysis                                 | High                                         |
|  **7** | Improve scalability experiments                                        | High                                         |
|  **8** | Correct Figs. 6–7                                                     | Mandatory presentation fix                   |
|  **9** | Add full-covariance bandwidth robustness                               | Medium/high                                  |
| **10** | Add external drawdown proxy robustness                                 | Medium                                       |
| **11** | Clarify daily-CVaR vs 21-day holding horizon                           | Medium                                       |
| **12** | Tighten wording and remove repetitions                                 | Final polishing                              |

### Target after revision

If you implement **items 1–8 well**, I would expect the manuscript to move from approximately **74/100 to 84–88/100**, because the main weaknesses are not a fundamentally defective model; they are mainly **positioning, benchmark strength, sensitivity coverage, and internal consistency**. The most important strategic change is to stop trying to make the empirical story about “performance superiority” and instead emphasize the much better supported result: **continuous-state robustness provides a tractable and interpretable regularization of highly unstable state-conditioned decisions**.
