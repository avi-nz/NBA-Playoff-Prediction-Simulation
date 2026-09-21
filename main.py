from nba_api.stats.endpoints import leaguestandings

from src.data.data_loader import load_regular_season_games, get_champion
from src.data.injury_loader import (
    get_injury_profiles,
    print_injury_profiles,
)
from src.models.elo import (
    EloModel,
    EloModelMoV,
    EloModelHCA,
    EloModelRecentForm,
    EloModelBayesian,
    EloModelInjury,
)
from src.sim.playoff_simulator import PlayoffSimulator
from src.data.teams import TEAM_ID_TO_NAME
from evaluation.brier_score import print_brier_report
from src.data.seasons import VALID_SEASONS

SLEEP_BETWEEN_SEASONS = 5
N_SIMULATIONS = 10000


def choose_season():
    """
    Prompt the user to select a valid NBA season.

    Returns:
        str: The selected season in the format 'YYYY-YY'.
    """

    print(f"Valid seasons: {VALID_SEASONS[0]} to {VALID_SEASONS[-1]}")

    season = input("\nEnter a season (e.g. 2024-25): ").strip()

    while season not in VALID_SEASONS:
        print(
            f"  Invalid season '{season}'. "
            f"Please enter a season between "
            f"{VALID_SEASONS[0]} and {VALID_SEASONS[-1]}."
        )
        season = input("  Enter a season: ").strip()

    return season


def choose_model():
    """
    Prompt the user to choose an Elo model.

    Returns:
        tuple[str, type]: The model name and corresponding Elo model class.
    """

    models = {
        "0": ("Model 0 — Baseline Elo",                  EloModel),
        "1": ("Model 1 — Margin of Victory Elo",         EloModelMoV),
        "2": ("Model 2 — Home Court Advantage",          EloModelHCA),
        "3": ("Model 3 — Recent Form",                   EloModelRecentForm),
        "4": ("Model 4 — Bayesian Team Strength",        EloModelBayesian),
        "5": ("Model 5 — Injury Modelling",              EloModelInjury),
    }

    print("\nAvailable models:")
    for key, (name, _) in models.items():
        print(f"  [{key}] {name}")

    choice = input("\nSelect a model: ").strip()

    while choice not in models:
        print(
            f"  Invalid choice '{choice}'. "
            f"Please enter one of: {', '.join(models.keys())}"
        )
        choice = input("  Select a model: ").strip()

    model_name, elo_model_class = models[choice]

    return model_name, elo_model_class


def train_model(season, elo_model_class):
    """
    Train the selected Elo model using regular season games.

    Args:
        season (str): NBA season to train on.
        elo_model_class: Elo model class to instantiate.

    Returns:
        EloModel: A trained Elo model.
    """

    # Load regular season games.
    games = load_regular_season_games(season)

    # Ensure games are processed chronologically.
    games = games.sort_values("DATE").reset_index(drop=True)

    # Train the selected Elo model.
    elo = elo_model_class(k=20, initial_rating=1500)
    elo.fit(games)

    print("Final Elo Ratings:")
    for team_id, rating in elo.get_rankings():
        print(
            f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} "
            f"{rating:.1f}"
        )

    return elo


def get_playoff_bracket(season):
    """
    Retrieve the top eight playoff seeds from each conference.

    Args:
        season (str): NBA season.

    Returns:
        tuple[list[int], list[int]]:
            Eastern and Western Conference team IDs.
    """

    # Get standings at the end of the regular season.
    standings = leaguestandings.LeagueStandings(
        season=season
    ).get_data_frames()[0]

    # Select the eight highest-seeded teams from each conference.
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

    return east, west


def setup_injury_model(elo, season, east, west):
    """
    Load and attach injury profiles when using the injury model.

    Args:
        elo: Trained Elo model.
        season (str): NBA season.
        east (list[int]): Eastern Conference playoff teams.
        west (list[int]): Western Conference playoff teams.

    Returns:
        EloModel: Elo model with injury profiles attached when applicable.
    """

    if isinstance(elo, EloModelInjury):
        print("\nLoading injury profiles...")

        playoff_teams = east + west

        profiles = get_injury_profiles(
            season,
            playoff_teams
        )

        # Print the injury profiles so we can inspect them.
        print_injury_profiles(profiles)

        # Attach profiles to the injury model.
        elo.injury_profiles = profiles

        # Reset the injury log before simulation.
        elo.reset_injury_log()

    return elo


def run_simulation(elo, east, west):
    """
    Simulate the NBA playoffs using Monte Carlo simulation.

    Args:
        elo: Trained Elo model.
        east (list[int]): Eastern Conference playoff teams.
        west (list[int]): Western Conference playoff teams.

    Returns:
        dict[int, float]: Championship probability for each team.
    """

    # Run Monte Carlo playoff simulation.
    sim = PlayoffSimulator(elo)

    results = sim.simulate_many(east, west, n_simulations=N_SIMULATIONS)

    # Display championship probabilities in descending order.
    print("\nChampionship Odds:")

    for team_id, prob in sorted(
        results.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(
            f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} "
            f"{prob * 100:.1f}%"
        )

    return results


def print_brier_score(season, results):
    """
    Calculate and display the Brier score for the model's predictions.

    Args:
        season (str): NBA season.
        results (dict): Simulated championship probabilities.
    """

    champion_id = get_champion(season)

    print_brier_report(results, champion_id, season=season)


def main():
    """
    Run the complete NBA championship prediction pipeline.

    The program:
        1. Prompts the user for a season.
        2. Prompts the user to choose an Elo model.
        3. Trains the model on regular season games.
        4. Retrieves the playoff bracket.
        5. Loads injury profiles if using the injury model.
        6. Simulates the playoffs.
        7. Evaluates the predictions using the Brier score.
    """

    season = choose_season()

    model_name, elo_model_class = choose_model()

    print(f"\nRunning {model_name}...\n")

    elo = train_model(season,elo_model_class)

    east, west = get_playoff_bracket(season)

    elo = setup_injury_model(elo, season, east, west)

    results = run_simulation(elo, east, west)

    print_brier_score(season, results)


if __name__ == "__main__":
    main()