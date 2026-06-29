from data_loader import load_regular_season_games
from elo import EloModel

# Load games
games = load_regular_season_games("2025-26")

# ensure chronological order
games = games.sort_values("DATE").reset_index(drop=True)

# Initialise model
elo = EloModel(k=20, initial_rating=1500)

# Fit model (actual season simulation)
elo.fit(games)

# Get final ratings (baseline Elo)
final_ratings = elo.get_ratings()

# Sort for standings-style output
rankings = elo.get_rankings()

for team, rating in rankings:
    print(team, rating)