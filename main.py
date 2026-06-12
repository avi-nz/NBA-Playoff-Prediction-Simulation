from nba_api.stats.endpoints import leaguegamelog
import pandas as pd

# Creates a request to the NBA stats API.
games = leaguegamelog.LeagueGameLog(
    season='2025-26',
    season_type_all_star='Regular Season'
)

df = games.get_data_frames()[0]

# sorts all rows by the GAME_DATE column
games_df = df.sort_values("GAME_DATE")

# Array which stores one dict for each game
grouped_games = []

for game_id, game in games_df.groupby("GAME_ID"):

    # make sure two teams exist for each game. If not then skip this game
    if len(game) != 2:
        continue

    team_1 = game.iloc[0]
    team_2 = game.iloc[1]

    grouped_games.append({
        # stores the game ID
        "GAME_ID": game_id,

        # team 1 & team 2 play on same day so either team could be used for this
        "DATE": team_1["GAME_DATE"],

        # Team names
        "TEAM_A": team_1["TEAM_NAME"],
        "TEAM_B": team_2["TEAM_NAME"],

        # stores the amount of points each team scores
        "TEAM_A_PTS": team_1["PTS"],
        "TEAM_B_PTS": team_2["PTS"]
    })

games = pd.DataFrame(grouped_games)
print(games)