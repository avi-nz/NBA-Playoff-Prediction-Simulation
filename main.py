from nba_api.stats.endpoints import leaguegamelog
import pandas as pd

games = leaguegamelog.LeagueGameLog(
    season='2025-26',
    season_type_all_star='Regular Season'
)

df = games.get_data_frames()[0]

print(df.head())