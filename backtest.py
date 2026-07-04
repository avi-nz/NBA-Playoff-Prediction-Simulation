from teams import TEAM_ID_TO_NAME


# ---------------------------------------------------------------------------
# Brier score — championship level
# ---------------------------------------------------------------------------

def championship_brier_score(predicted_probs, actual_champion):
    """
    Computes the Brier score for a single season's championship forecast.

    For each playoff team the model assigned a probability p of winning
    the championship. The actual outcome is 1 for the real champion and
    0 for everyone else. The score is the mean squared error across all
    teams:

        Brier = sum((p_i - outcome_i)^2)

    A perfect model scores 0.0.
    For a 16-team playoff, a naive model assigning every team an equal
    1/16 championship probability has a Brier score of

    (1 - 1/16)^2 + 15*(1/16)^2 = 0.9375

    Lower is better.

    Parameters
    ----------
    predicted_probs : dict
        Output of PlayoffSimulator.simulate_many().
        Format: {team_id (int): probability (float)}

    actual_champion : int
        TEAM_ID of the team that actually won the championship.
        From load_playoff_games(season)["champion"].

    Returns
    -------
    float
        Multiclass Brier score for this season.

        The score ranges from 0.0 (perfect forecast) to 2.0 (worst possible
        forecast, assigning 100% probability to the wrong team).
    """

    total = 0.0

    for team_id, p in predicted_probs.items():
        outcome = 1 if int(team_id) == int(actual_champion) else 0
        total += (p - outcome) ** 2

    return total


def multi_season_brier_score(season_results):
    """
    Averages championship Brier scores across multiple seasons to produce
    a single model-level score for comparison.

    This is the main number for comparing Model 0 vs Model 1 vs Model 2,
    etc. A model that is genuinely better at forecasting championship
    probability will have a lower average Brier score.

    Parameters
    ----------
    season_results : list of dicts
        Each dict must contain:
            "predicted_probs" : dict {team_id (int): probability (float)}
            "actual_champion" : int (TEAM_ID)

        One dict per season. Build this by running simulate_many() and
        load_playoff_games() for each historical season.

    Returns
    -------
    float
        Mean Brier score across all seasons.

    Example
    -------
    season_results = [
        {
            "predicted_probs": {1610612760: 0.28, 1610612738: 0.21, ...},
            "actual_champion": 1610612738
        },
        ...
    ]
    score = multi_season_brier_score(season_results)
    print(f"Model 0 Brier: {score:.4f}")
    """

    if not season_results:
        raise ValueError("season_results is empty.")

    scores = [
        championship_brier_score(r["predicted_probs"], r["actual_champion"])
        for r in season_results
    ]

    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def print_brier_report(predicted_probs, actual_champion, season=None):
    """
    Prints a human-readable Brier score report for a single season,
    showing every playoff team's predicted probability, actual outcome,
    and individual squared error contribution.

    Parameters
    ----------
    predicted_probs : dict
        {team_id (int): probability (float)}

    actual_champion : int
        TEAM_ID of the real champion.

    season : str, optional
        Season label for the header, e.g. "2024-25".
    """

    score  = championship_brier_score(predicted_probs, actual_champion)
    header = f"BRIER SCORE REPORT" + (f"  —  {season}" if season else "")

    print(f"\n{'='*60}")
    print(f"  {header}")
    print(f"{'='*60}")
    print(f"  {'TEAM':<30} {'PRED %':>7}  {'OUTCOME':>8}  {'SQ ERROR':>9}")
    print(f"  {'-'*58}")

    ranked = sorted(predicted_probs.items(), key=lambda x: x[1], reverse=True)

    for team_id, p in ranked:
        outcome      = 1 if team_id == actual_champion else 0
        sq_error     = (p - outcome) ** 2
        name         = TEAM_ID_TO_NAME.get(team_id, str(team_id))
        champion_flag = "  🏆" if outcome == 1 else ""
        print(f"  {name:<30} {p*100:>6.1f}%  {outcome:>8}  {sq_error:>9.4f}{champion_flag}")

    print(f"  {'-'*58}")
    print(f"  {'Brier Score':<30} {' ':>7}  {' ':>8}  {score:>9.4f}")

    n_teams = len(predicted_probs)
    uniform_baseline = (1 - 1 / n_teams) ** 2 + (n_teams - 1) * (1 / n_teams) ** 2

    print(f"\n  Reference: uniform baseline (1/{n_teams} each) = {uniform_baseline:.4f}")