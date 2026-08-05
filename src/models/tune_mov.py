"""
tune_mov.py

Finds the optimal parameters (a, b, c, d) for the EloModelMoV
margin-of-victory multiplier:

    mov_multiplier = (point_diff + a)^b / (c + d * elo_diff)

Uses rolling-origin cross-validation to avoid overfitting:
for each test season, parameters are evaluated only on that season
after being tuned on all seasons before it. This ensures every
evaluation is genuinely out-of-sample.

Also compares simpler multiplier variants to check whether the full
four-parameter formula is actually justified.
"""

import time
import numpy as np
from scipy.optimize import minimize
from src.data.data_loader import load_regular_season_games
from src.models.elo import EloModel, EloModelMoV
from src.data.seasons import VALID_SEASONS

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Seasons used to tune parameters — held out from final evaluation
TRAIN_SEASONS = VALID_SEASONS[:25]   # 1996-97 to 2020-21
TEST_SEASONS  = VALID_SEASONS[25:]   # 2021-22 to 2025-26

# ---------------------------------------------------------------------------
# Load all seasons upfront
# ---------------------------------------------------------------------------

print("Loading regular season games for all seasons...")
print("(This only happens once — the optimiser reuses this data)\n")

season_data = {}  # season string -> DataFrame

for i, season in enumerate(VALID_SEASONS):
    print(f"  [{i+1}/{len(VALID_SEASONS)}] {season}")
    try:
        games = load_regular_season_games(season)
        season_data[season] = games.sort_values("DATE").reset_index(drop=True)
        time.sleep(1)
    except Exception as e:
        print(f"    ERROR: {e} — skipping")

train_games = [season_data[s] for s in TRAIN_SEASONS if s in season_data]
test_games  = [season_data[s] for s in TEST_SEASONS  if s in season_data]
all_games   = [season_data[s] for s in VALID_SEASONS  if s in season_data]

print(f"\nLoaded {len(season_data)} seasons "
      f"({len(train_games)} train, {len(test_games)} test).\n")


# ---------------------------------------------------------------------------
# Core evaluation — game-level Brier score for a list of seasons
# ---------------------------------------------------------------------------

def evaluate_mov(seasons_list, a, b, c, d):
    """
    Computes the average per-game Brier score for EloModelMoV with the
    given parameters across a list of season DataFrames.

    Each game is predicted before ratings are updated, making every
    prediction genuinely out-of-sample relative to prior games.
    """

    if a <= 0 or b <= 0 or c <= 0 or d <= 0:
        return 999.0

    total_brier = 0.0
    total_games = 0

    for games in seasons_list:
        elo = EloModelMoV(k=20, initial_rating=1500, a=a, b=b, c=c, d=d)
        elo.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            prob   = elo.win_probability(home, away)
            actual = 1 if row["HOME_PTS"] > row["AWAY_PTS"] else 0

            total_brier += (prob - actual) ** 2
            total_games += 1

            winner     = home if actual == 1 else away
            point_diff = abs(int(row["HOME_PTS"]) - int(row["AWAY_PTS"]))
            elo.update_ratings(home, away, winner, point_diff)

    return total_brier / total_games


def evaluate_model0(seasons_list):
    """Game-level Brier score for baseline EloModel (no MoV)."""

    total_brier = 0.0
    total_games = 0

    for games in seasons_list:
        elo = EloModel(k=20, initial_rating=1500)
        elo.initialize_teams(games)

        for _, row in games.iterrows():
            home   = row["HOME_TEAM"]
            away   = row["AWAY_TEAM"]
            prob   = elo.win_probability(home, away)
            actual = 1 if row["HOME_PTS"] > row["AWAY_PTS"] else 0

            total_brier += (prob - actual) ** 2
            total_games += 1

            winner = home if actual == 1 else away
            elo.update_ratings(home, away, winner)

    return total_brier / total_games


# ---------------------------------------------------------------------------
# Multiplier variant evaluation (for comparison table)
# ---------------------------------------------------------------------------

def evaluate_custom_multiplier(seasons_list, multiplier_fn):
    """
    Evaluates an arbitrary MoV multiplier function.

    multiplier_fn(point_diff, elo_diff) -> float
    """

    total_brier = 0.0
    total_games = 0

    for games in seasons_list:
        elo = EloModel(k=20, initial_rating=1500)
        elo.initialize_teams(games)

        for _, row in games.iterrows():
            home   = row["HOME_TEAM"]
            away   = row["AWAY_TEAM"]
            prob   = elo.win_probability(home, away)
            actual = 1 if row["HOME_PTS"] > row["AWAY_PTS"] else 0

            total_brier += (prob - actual) ** 2
            total_games += 1

            winner     = home if actual == 1 else away
            loser      = away if actual == 1 else home
            point_diff = abs(int(row["HOME_PTS"]) - int(row["AWAY_PTS"]))
            elo_diff   = elo.ratings[winner] - elo.ratings[loser]

            prob_w    = elo.win_probability(winner, loser)
            actual_w  = 1
            multiplier = multiplier_fn(point_diff, elo_diff)

            elo.ratings[winner] += elo.k * multiplier * (actual_w - prob_w)
            elo.ratings[loser]  += elo.k * multiplier * (0 - (1 - prob_w))

    return total_brier / total_games


# ---------------------------------------------------------------------------
# Multiplier variants
# ---------------------------------------------------------------------------

VARIANTS = {
    "Model 0 (no MoV)":        lambda pd, ed: 1.0,
    "log(mov + 1)":             lambda pd, ed: np.log(pd + 1),
    "mov ** 0.7":               lambda pd, ed: pd ** 0.7,
    "538 formula":              lambda pd, ed: (pd + 3) ** 0.8 / (7.5 + 0.006 * ed),
}

# ---------------------------------------------------------------------------
# Baseline scores
# ---------------------------------------------------------------------------

print("="*60)
print("  STEP 1 — BASELINE SCORES (all 30 seasons)")
print("="*60)
print(f"  Model 0 (train) : {evaluate_model0(train_games):.6f}")
print(f"  Model 0 (test)  : {evaluate_model0(test_games):.6f}")
print()

# ---------------------------------------------------------------------------
# Optimise on training seasons only
# ---------------------------------------------------------------------------

print("="*60)
print("  STEP 2 — OPTIMISE ON TRAIN SEASONS (1996-97 to 2020-21)")
print("="*60)

x0 = np.array([3.0, 0.8, 7.5, 0.006])

print(f"  Starting params : a={x0[0]}, b={x0[1]}, c={x0[2]}, d={x0[3]}")
print(f"  Starting score  : {evaluate_mov(train_games, *x0):.6f}\n")

result = minimize(
    lambda params: evaluate_mov(train_games, *params),
    x0=x0,
    method="Nelder-Mead",
    options={
        "xatol": 1e-4,
        "fatol": 1e-6,
        "maxiter": 1000,
        "disp": True,
    }
)

a_opt, b_opt, c_opt, d_opt = result.x

print(f"\n  Tuned params : a={a_opt:.4f}, b={b_opt:.4f}, "
      f"c={c_opt:.4f}, d={d_opt:.4f}")

# ---------------------------------------------------------------------------
# Rolling-origin cross-validation
# ---------------------------------------------------------------------------

print()
print("="*60)
print("  STEP 3 — ROLLING-ORIGIN CROSS-VALIDATION")
print("="*60)
print("  For each test season, parameters are fit on all prior seasons")
print("  and then evaluated on the unseen test season.\n")

ROLLING_START = 6  # minimum seasons of training data before testing

rolling_scores = {"538": [], "tuned": [], "model0": []}

for i in range(ROLLING_START, len(VALID_SEASONS)):
    test_season = VALID_SEASONS[i]
    if test_season not in season_data:
        continue

    cv_train = [season_data[s] for s in VALID_SEASONS[:i] if s in season_data]
    cv_test  = [season_data[test_season]]

    # Re-optimise on the rolling training window
    cv_result = minimize(
        lambda params: evaluate_mov(cv_train, *params),
        x0=x0,
        method="Nelder-Mead",
        options={"xatol": 1e-3, "fatol": 1e-5, "maxiter": 500, "disp": False}
    )

    cv_a, cv_b, cv_c, cv_d = cv_result.x

    score_538   = evaluate_mov(cv_test, 3.0, 0.8, 7.5, 0.006)
    score_tuned = evaluate_mov(cv_test, cv_a, cv_b, cv_c, cv_d)
    score_m0    = evaluate_model0(cv_test)

    rolling_scores["538"].append(score_538)
    rolling_scores["tuned"].append(score_tuned)
    rolling_scores["model0"].append(score_m0)

    print(f"  {test_season}  model0={score_m0:.5f}  "
          f"538={score_538:.5f}  tuned={score_tuned:.5f}")

avg_538   = np.mean(rolling_scores["538"])
avg_tuned = np.mean(rolling_scores["tuned"])
avg_m0    = np.mean(rolling_scores["model0"])

print(f"\n  Rolling average:")
print(f"    Model 0  : {avg_m0:.6f}")
print(f"    538      : {avg_538:.6f}  ({avg_538 - avg_m0:+.6f} vs Model 0)")
print(f"    Tuned    : {avg_tuned:.6f}  ({avg_tuned - avg_m0:+.6f} vs Model 0)")

# ---------------------------------------------------------------------------
# Multiplier comparison table (all 30 seasons)
# ---------------------------------------------------------------------------

print()
print("="*60)
print("  STEP 4 — MULTIPLIER COMPARISON (all 30 seasons)")
print("="*60)
print(f"  {'Variant':<30} {'Train Brier':>12}  {'Test Brier':>12}")
print(f"  {'-'*56}")

for name, fn in VARIANTS.items():
    train_score = evaluate_custom_multiplier(train_games, fn)
    test_score  = evaluate_custom_multiplier(test_games, fn)
    print(f"  {name:<30} {train_score:>12.6f}  {test_score:>12.6f}")

# Tuned 4-param
tuned_train = evaluate_mov(train_games, a_opt, b_opt, c_opt, d_opt)
tuned_test  = evaluate_mov(test_games,  a_opt, b_opt, c_opt, d_opt)
print(f"  {'Tuned 4-param':<30} {tuned_train:>12.6f}  {tuned_test:>12.6f}")

print()
print(f"  Note: train = 1996-97 to 2020-21, test = 2021-22 to 2025-26")
print(f"  A model that improves on train but not test is overfitting.")

# ---------------------------------------------------------------------------
# Final recommendation
# ---------------------------------------------------------------------------

print()
print("="*60)
print("  TUNED PARAMETERS (fit on training seasons only)")
print("="*60)
print(f"  {'Parameter':<12} {'538':>12}  {'Tuned':>12}")
print(f"  {'-'*38}")
print(f"  {'a':<12} {3.0:>12.4f}  {a_opt:>12.4f}")
print(f"  {'b':<12} {0.8:>12.4f}  {b_opt:>12.4f}")
print(f"  {'c':<12} {7.5:>12.4f}  {c_opt:>12.4f}")
print(f"  {'d':<12} {0.006:>12.4f}  {d_opt:>12.4f}")
print(f"""
To use the tuned parameters in run_backtest.py:

    elo = EloModelMoV(k=20, initial_rating=1500,
                      a={a_opt:.4f}, b={b_opt:.4f},
                      c={c_opt:.4f}, d={d_opt:.4f})
""")