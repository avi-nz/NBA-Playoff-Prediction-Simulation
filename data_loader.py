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
    neutral_games = []

    for game_id, game in games_df.groupby("GAME_ID"):

        home = game[game["MATCHUP"].str.contains("vs.", regex=False)]
        away = game[game["MATCHUP"].str.contains("@", regex=False)]

        # Case 1: normal home/away game
        if len(home) == 1 and len(away) == 1:

            home = home.iloc[0]
            away = away.iloc[0]

            grouped_games.append({
                "GAME_ID": game_id,
                "DATE": home["GAME_DATE"],

                "HOME_TEAM": home["TEAM_NAME"],
                "AWAY_TEAM": away["TEAM_NAME"],

                "HOME_PTS": home["PTS"],
                "AWAY_PTS": away["PTS"],

                "SITE_TYPE": "HOME_AWAY"
            })

        # Case 2: neutral site game (NBA Cup / special games)
        # len of away = 2 cause both teams are marked as away when there is a neutral site.
        elif len(home) == 0 and len(away) == 2:

            # in neutral games, BOTH rows usually have "@"
            # so we just take both teams safely
            team_a = game.iloc[0]
            team_b = game.iloc[1]

            neutral_games.append(game_id)

            grouped_games.append({
                "GAME_ID": game_id,
                "DATE": team_a["GAME_DATE"],

                "HOME_TEAM": "TEAM_A",
                "AWAY_TEAM": "TEAM_B",

                "HOME_PTS": team_a["PTS"],
                "AWAY_PTS": team_b["PTS"],

                "SITE_TYPE": "NEUTRAL"
            })

        # unexpected structure - log it
        else:
            print(f"Unexpected game structure: {game_id}")
            print(game[["TEAM_NAME", "MATCHUP"]])

    print(f"Neutral games found: {len(neutral_games)}")

    return pd.DataFrame(grouped_games)