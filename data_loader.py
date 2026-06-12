from nba_api.stats.endpoints import scoreboardv2
import pandas as pd

def load_regular_season_games(season):
    """
    Loads NBA regular season games using ScoreboardV2.
    Returns one row per game with explicit home/away structure.
    """

    # ScoreboardV2 is date-based, so we must loop through dates in season
    # We'll collect all games into this list
    all_games = []

