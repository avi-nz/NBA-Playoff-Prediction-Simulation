"""
compare_models.py

Statistically compares two models using their per-season Brier scores
stored in the backtest result JSON files.

Tests used:
    - Paired t-test          (assumes normal distribution of differences)
    - Wilcoxon signed-rank   (no normality assumption, more robust)
    - Bootstrap CI           (non-parametric, recommended)

The unit of analysis is one Brier score per season — 30 observations
per model. The 10,000 simulations per season are already averaged into
a single score inside the JSON, so they are not treated as independent.
"""

import json
import numpy as np
from scipy.stats import ttest_rel, wilcoxon


# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------

def load_scores(filepath):
    """
    Load per-season Brier scores from a backtest JSON file.

    Returns a dict mapping season string to Brier score.
    """
    with open(filepath, "r") as f:
        results = json.load(f)
    return {r["season"]: r["brier_score"] for r in results if "brier_score" in r}


MODEL_FILES = {
    "Model 0 — Baseline Elo":         "../results/backtest_model0.json",
    "Model 2 — Home Court Advantage":  "../results/backtest_model2.json",
}

print("Loading results...")
all_scores = {name: load_scores(path) for name, path in MODEL_FILES.items()}

# Find seasons present in all models
common_seasons = sorted(
    set.intersection(*[set(s.keys()) for s in all_scores.values()])
)

print(f"Seasons in common: {len(common_seasons)}\n")

model_names = list(all_scores.keys())
name_a = model_names[0]
name_b = model_names[1]

scores_a = np.array([all_scores[name_a][s] for s in common_seasons])
scores_b = np.array([all_scores[name_b][s] for s in common_seasons])
diff     = scores_a - scores_b   # positive = model A was worse that season


# ---------------------------------------------------------------------------
# Season-by-season comparison table
# ---------------------------------------------------------------------------

print("="*70)
print(f"  SEASON-BY-SEASON COMPARISON")
print("="*70)
print(f"  {'SEASON':<12} {'Model 0':>10}  {'Model 2':>10}  {'DIFF (0-2)':>12}  {'WINNER'}")
print(f"  {'-'*65}")

a_wins = 0
b_wins = 0

for season, d, sa, sb in zip(common_seasons, diff, scores_a, scores_b):
    winner = "Model 0" if sa < sb else "Model 2"
    if sa < sb:
        a_wins += 1
    else:
        b_wins += 1
    print(f"  {season:<12} {sa:>10.4f}  {sb:>10.4f}  {d:>+12.4f}  {winner}")

print(f"  {'-'*65}")
print(f"  {'Average':<12} {scores_a.mean():>10.4f}  {scores_b.mean():>10.4f}  "
      f"{diff.mean():>+12.4f}")
print(f"\n  Model 0 wins : {a_wins}/{len(common_seasons)} seasons")
print(f"  Model 2 wins : {b_wins}/{len(common_seasons)} seasons")


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

print()
print("="*70)
print("  SIGNIFICANCE TESTS  (H0: no difference between models)")
print("="*70)

# Paired t-test
t_stat, p_ttest = ttest_rel(scores_a, scores_b)
print(f"\n  Paired t-test")
print(f"    T-statistic : {t_stat:.4f}")
print(f"    P-value     : {p_ttest:.4f}")
print(f"    {'Significant at p<0.05' if p_ttest < 0.05 else 'Not significant at p<0.05'}")

# Wilcoxon signed-rank test
stat_w, p_wilcoxon = wilcoxon(scores_a, scores_b)
print(f"\n  Wilcoxon signed-rank test")
print(f"    Statistic   : {stat_w:.4f}")
print(f"    P-value     : {p_wilcoxon:.4f}")
print(f"    {'Significant at p<0.05' if p_wilcoxon < 0.05 else 'Not significant at p<0.05'}")

# Bootstrap confidence interval
rng     = np.random.default_rng(seed=42)
n_boot  = 10000
means   = np.array([
    rng.choice(diff, size=len(diff), replace=True).mean()
    for _ in range(n_boot)
])
ci = np.percentile(means, [2.5, 97.5])

print(f"\n  Bootstrap confidence interval (10,000 resamples)")
print(f"    Mean difference (Model 0 - Model 2) : {diff.mean():+.4f}")
print(f"    95% CI : ({ci[0]:+.4f}, {ci[1]:+.4f})")
if ci[0] > 0:
    print(f"    CI is entirely above 0 — Model 2 is consistently better")
elif ci[1] < 0:
    print(f"    CI is entirely below 0 — Model 0 is consistently better")
else:
    print(f"    CI crosses 0 — difference is not statistically significant")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print("="*70)
print("  SUMMARY")
print("="*70)
print(f"  Absolute improvement  : {diff.mean():+.4f}")
print(f"  Relative improvement  : {diff.mean() / scores_a.mean() * 100:+.2f}%")
print(f"  Seasons Model 2 wins  : {b_wins}/{len(common_seasons)}")
print(f"  Paired t-test p-value : {p_ttest:.4f}")
print(f"  Wilcoxon p-value      : {p_wilcoxon:.4f}")
print(f"  Bootstrap 95% CI      : ({ci[0]:+.4f}, {ci[1]:+.4f})")