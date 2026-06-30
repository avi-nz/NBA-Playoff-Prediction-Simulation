from nba_api.stats.endpoints import leaguestandings
from data_loader import load_regular_season_games
from elo import EloModel
from playoff_simulator import PlayoffSimulator
from teams import TEAM_ID_TO_NAME

SEASON = "2025-26"

# Train Elo on regular season games
games = load_regular_season_games(SEASON)
games = games.sort_values("DATE").reset_index(drop=True)

elo = EloModel(k=20, initial_rating=1500)
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