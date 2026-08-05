from nba_api.stats.endpoints import leaguestandings
from src.data.data_loader import load_regular_season_games, get_champion
from src.models.elo import EloModel, EloModelMoV, EloModelHCA
from src.sim.playoff_simulator import PlayoffSimulator
from src.data.teams import TEAM_ID_TO_NAME
from evaluation.brier_score import print_brier_report
from src.data.seasons import VALID_SEASONS


def choose_season():
    """
    Prompt the user to select a valid NBA season.

    Returns:
        str: The selected season in the format 'YYYY-YY'.
    """

    # Season selection
    print(f"Valid seasons: {VALID_SEASONS[0]} to {VALID_SEASONS[-1]}")

    season = input("\nEnter a season (e.g. 2024-25): ").strip()

    while season not in VALID_SEASONS:
        print(f"  Invalid season '{season}'. Please enter a season between {VALID_SEASONS[0]} and {VALID_SEASONS[-1]}.")
        season = input("  Enter a season: ").strip()

    return season


def choose_model():
    """
    Prompt the user to choose an Elo model.

    Returns:
        tuple[str, type]: The model name and corresponding Elo model class.
    """

    # Model selection
    models = {
        "0": ("Model 0 — Baseline Elo", EloModel),
        "1": ("Model 1 — Margin of Victory Elo", EloModelMoV),
        "2": ("Model 2 — Home Court Advantage", EloModelHCA),
    }

    # prints all the models that are available
    print("\nAvailable models:")
    for key, (name, _) in models.items():
        print(f"  [{key}] {name}")

    choice = input("\nSelect a model: ").strip()

    # if the user did not select a valid model, get them to try again
    while choice not in models:
        print(f"  Invalid choice '{choice}'. Please enter one of: {', '.join(models.keys())}")
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

    # load in the games for the chosen season
    games = load_regular_season_games(season)
    # Ensure games are processed in chronological order.
    games = games.sort_values("DATE").reset_index(drop=True)

    # train games on the chosen elo model
    elo = elo_model_class(k=20, initial_rating=1500)
    elo.fit(games)

    print("Final Elo Ratings:")
    for team_id, rating in elo.get_rankings():
        print(f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} {rating:.1f}")

    return elo


def get_playoff_bracket(season):
    """
    Retrieve the top eight playoff seeds from each conference.

    Args:
        season (str): NBA season.

    Returns:
        tuple[list[int], list[int]]: Eastern and Western Conference team IDs.
    """

    # Get standings at the end of the season
    standings = leaguestandings.LeagueStandings(season=season).get_data_frames()[0]

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

    # Run Monte Carlo playoff simulation
    sim = PlayoffSimulator(elo)
    results = sim.simulate_many(east, west, n_simulations=10000)

    # Display championship probabilities in descending order.
    print("\nChampionship Odds:")
    for team_id, prob in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} {prob * 100:.1f}%")

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
        5. Simulates the playoffs.
        6. Evaluates the predictions using the Brier score.
    """

    season = choose_season()

    model_name, elo_model_class = choose_model()
    print(f"\nRunning {model_name}...\n")

    elo = train_model(season, elo_model_class)

    east, west = get_playoff_bracket(season)

    results = run_simulation(elo, east, west)

    print_brier_score(season, results)


if __name__ == "__main__":
    main()