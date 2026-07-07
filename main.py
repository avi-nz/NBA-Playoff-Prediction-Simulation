from nba_api.stats.endpoints import leaguestandings
from data_loader import load_regular_season_games, get_champion
from elo import EloModel, EloModelMoV
from playoff_simulator import PlayoffSimulator
from teams import TEAM_ID_TO_NAME
from brier_score import print_brier_report
from seasons import VALID_SEASONS


# Season selection
print(f"Valid seasons: {VALID_SEASONS[0]} to {VALID_SEASONS[-1]}")

season = input("\nEnter a season (e.g. 2024-25): ").strip()

while season not in VALID_SEASONS:
    print(f"  Invalid season '{season}'. Please enter a season between {VALID_SEASONS[0]} and {VALID_SEASONS[-1]}.")
    season = input("  Enter a season: ").strip()

SEASON = season

# Model selection
MODELS = {
    "0": ("Model 0 — Baseline Elo", EloModel),
    "1": ("Model 1 — Margin of Victory Elo", EloModelMoV),
}

print("\nAvailable models:")
for key, (name, _) in MODELS.items():
    print(f"  [{key}] {name}")

choice = input("\nSelect a model: ").strip()

while choice not in MODELS:
    print(f"  Invalid choice '{choice}'. Please enter one of: {', '.join(MODELS.keys())}")
    choice = input("  Select a model: ").strip()

model_name, EloModelClass = MODELS[choice]
print(f"\nRunning {model_name}...\n")


# Train Elo on regular season games
games = load_regular_season_games(SEASON)
games = games.sort_values("DATE").reset_index(drop=True)

elo = EloModelClass(k=20, initial_rating=1500)
elo.fit(games)

print("Final Elo Ratings:")
for team_id, rating in elo.get_rankings():
    print(f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} {rating:.1f}")

# Get the playoff bracket (top 8 seeds per conference)
standings = leaguestandings.LeagueStandings(season=SEASON).get_data_frames()[0]

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

# Run Monte Carlo playoff simulation
sim = PlayoffSimulator(elo)
results = sim.simulate_many(east, west, n_simulations=10000)

print("\nChampionship Odds:")
for team_id, prob in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{TEAM_ID_TO_NAME.get(team_id, team_id):25s} {prob * 100:.1f}%")

# print the brier score
champion_id = get_champion(SEASON)
print_brier_report(results, champion_id, season=SEASON)