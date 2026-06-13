from nba_api.stats.endpoints import leaguegamelog
import pandas as pd

def load_regular_season_games(season):

    games = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star='Regular Season'
    )

    df = games.get_data_frames()[0]
    games_df = df.sort_values("GAME_DATE")

    grouped_games = []
    bad_games = []

    for game_id, game in games_df.groupby("GAME_ID"):

        home = game[game["MATCHUP"].str.contains("vs.", regex=False)]
        away = game[game["MATCHUP"].str.contains("@", regex=False)]

        if len(home) != 1 or len(away) != 1:
            bad_games.append(game_id)
            continue

        home = home.iloc[0]
        away = away.iloc[0]

        grouped_games.append({
            "GAME_ID": game_id,
            "DATE": home["GAME_DATE"],

            "HOME_TEAM": home["TEAM_NAME"],
            "AWAY_TEAM": away["TEAM_NAME"],

            "HOME_PTS": home["PTS"],
            "AWAY_PTS": away["PTS"]
        })

    print(f"Bad games found: {len(bad_games)}")

    return pd.DataFrame(grouped_games)