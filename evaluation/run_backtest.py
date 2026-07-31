import json
import os
import time
from nba_api.stats.endpoints import leaguestandings
from src.data.data_loader import load_regular_season_games, get_champion
from src.models.elo import EloModel, EloModelMoV, EloModelHCA
from src.sim.playoff_simulator import PlayoffSimulator
from evaluation.brier_score import championship_brier_score
from src.data.teams import TEAM_ID_TO_NAME
from src.sim.seasons import VALID_SEASONS


# Seconds to wait between seasons to avoid NBA API rate limiting.
SLEEP_BETWEEN_SEASONS = 5

N_SIMULATIONS = 10000


def choose_model():
    """
    Prompt the user to choose an Elo model.

    Returns:
        tuple[str, type, str]: The model name, Elo model class, and results file path.
    """

    models = {
        "0": ("Model 0 — Baseline Elo", EloModel, "../results/backtest_model0.json"),
        "1": ("Model 1 — Margin of Victory Elo", EloModelMoV, "../results/backtest_model1.json"),
        "2": ("Model 2 — Home Court Advantage", EloModelHCA, "../results/backtest_model2.json"),
    }

    print("\nAvailable models:")
    for key, (name, _, _) in models.items():
        print(f"  [{key}] {name}")

    choice = input("\nSelect a model: ").strip()

    while choice not in models:
        print(f"  Invalid choice '{choice}'. Please enter one of: {', '.join(models.keys())}")
        choice = input("  Select a model: ").strip()

    model_name, elo_model_class, results_file = models[choice]
    print(f"\nRunning backtest for {model_name}...\n")

    return model_name, elo_model_class, results_file


def load_existing_results(results_file):
    """
    Load existing backtest results from disk, if available.

    Args:
        results_file (str): Path to the JSON results file.

    Returns:
        list[dict]: Previously completed season results.
    """

    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def run_season(season, elo_model_class):
    """
    Run the full backtest pipeline for one season.

    Args:
        season (str): NBA season string (e.g. '2023-24').
        elo_model_class: Elo model class to instantiate.

    Returns:
        dict: Season result with keys: season, brier_score, champion_id,
              champion_name, champion_predicted_prob, predicted_probs.
    """

    print(f"\n{'=' * 52}")
    print(f"{season}")
    print(f"{'=' * 52}")

    # --- Regular season games ---
    print("  Loading regular season games...")
    games = load_regular_season_games(season)
    games = games.sort_values("DATE").reset_index(drop=True)

    # --- Elo model ---
    print("  Training Elo model...")
    elo = elo_model_class(k=20, initial_rating=1500)
    elo.fit(games)

    # --- Playoff seeds ---
    print("  Fetching playoff seedings...")
    time.sleep(1)  # small pause before the standings call
    standings = leaguestandings.LeagueStandings(season=season).get_data_frames()[0]

    east = (
        standings[standings["Conference"] == "East"]
        .sort_values("PlayoffRank")
        .head(8)["TeamID"]
        .tolist()
    )

    west = (
        standings[standings["Conference"] == "West"]
        .sort_values("PlayoffRank")
        .head(8)["TeamID"]
        .tolist()
    )

    # Monte Carlo simulation
    print(f"  Running {N_SIMULATIONS:,} simulations...")
    sim = PlayoffSimulator(elo)
    predicted_probs = sim.simulate_many(east, west, n_simulations=N_SIMULATIONS)

    # Actual champion
    print("  Fetching actual champion...")
    time.sleep(1)
    champion_id = get_champion(season)
    champion_name = TEAM_ID_TO_NAME.get(champion_id, str(champion_id))

    # Brier score
    brier = championship_brier_score(predicted_probs, champion_id)
    champion_prob = predicted_probs.get(champion_id, 0.0)

    print(f"  Champion : {champion_name}")
    print(f"  Model prob for champion : {champion_prob * 100:.1f}%")
    print(f"  Brier score : {brier:.4f}")

    return {
        "season": season,
        "brier_score": round(brier, 6),
        "champion_id": champion_id,
        "champion_name": champion_name,
        "champion_predicted_prob": round(champion_prob, 6),
        # Store probs with string keys so JSON can serialise them
        "predicted_probs": {
            str(k): round(v, 6) for k, v in predicted_probs.items()
        },
    }


def save_results(results, results_file):
    """
    Save backtest results to disk.

    Args:
        results (list[dict]): All completed season results.
        results_file (str): Path to the JSON results file.
    """

    os.makedirs("results", exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)


def run_all_seasons(elo_model_class, results_file):
    """
    Iterate over all valid seasons, skipping already-completed ones,
    and save results after each season.

    Args:
        elo_model_class: Elo model class to use for each season.
        results_file (str): Path to the JSON results file.

    Returns:
        list[dict]: All completed season results.
    """

    all_results = load_existing_results(results_file)
    completed_seasons = {r["season"] for r in all_results}

    for season in VALID_SEASONS:

        if season in completed_seasons:
            print(f"Skipping {season} (already completed)")
            continue

        try:
            result = run_season(season, elo_model_class)
            all_results.append(result)
            save_results(all_results, results_file)  # save after every season

        except Exception as e:
            print(f"  ERROR on {season}: {e}")
            print(f"  Skipping and continuing...")

        time.sleep(SLEEP_BETWEEN_SEASONS)

    return all_results


def print_summary(all_results, model_name):
    """
    Print a summary table of backtest results across all seasons.

    Args:
        all_results (list[dict]): All completed season results.
        model_name (str): Name of the model used.
    """

    completed = [r for r in all_results if "brier_score" in r]

    if not completed:
        print("\nNo completed seasons to summarise.")
        return

    avg_brier = sum(r["brier_score"] for r in completed) / len(completed)

    print(f"\n{'=' * 52}")
    print(f"  {model_name.upper()} — BACKTEST SUMMARY")
    print(f"{'=' * 52}")
    print(f"  {'SEASON':<12} {'CHAMPION':<28} {'PRED %':>7}  {'BRIER':>8}")
    print(f"  {'-' * 58}")

    for r in sorted(completed, key=lambda x: x["season"]):
        print(
            f"  {r['season']:<12} "
            f"{r['champion_name']:<28} "
            f"{r['champion_predicted_prob'] * 100:>6.1f}%  "
            f"{r['brier_score']:>8.4f}"
        )

    n = len(completed)
    baseline = (1 - 1 / 16) ** 2 + 15 * (1 / 16) ** 2  # 0.9375

    print(f"  {'-' * 58}")
    print(f"  {'Average':<12} {' ':<28} {' ':>7}  {avg_brier:>8.4f}")
    print(f"\n  Seasons completed : {n}")
    print(f"  Uniform baseline  : {baseline:.4f}")
    print(f"  Model avg Brier   : {avg_brier:.4f}")
    print(f"  vs baseline       : {avg_brier - baseline:+.4f}")


def main():
    """
    Run the complete NBA backtest pipeline.

    The program:
        1. Prompts the user to choose an Elo model.
        2. Loads any existing results for that model.
        3. Runs the pipeline for each unprocessed season.
        4. Saves results after each season.
        5. Prints a summary table.
    """

    model_name, elo_model_class, results_file = choose_model()
    print(f"\nRunning backtest for {model_name}...\n")

    all_results = run_all_seasons(elo_model_class, results_file)

    print_summary(all_results, model_name)


if __name__ == "__main__":
    main()