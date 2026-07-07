import pandas as pd
import math

"""
elo.py

Implements a basic Elo rating system used to estimate NBA team strength.

The model processes regular season games chronologically, updates team
ratings after every match, and stores a complete history of Elo ratings
for later analysis and playoff simulation.
"""

class EloModel:
    """
    Implements a basic Elo rating system for NBA teams.

    Each team begins with the same initial rating and has its rating
    updated after every game based on the expected and actual outcome.

    This implementation uses the standard Elo expected probability
    equation and records the rating history after every game so that
    team performance can be analysed throughout the season.
    """

    def __init__(self, k = 20, initial_rating = 1500):
        """
        Initialise the Elo model.

        Parameters
        ----------
        k : int, optional
            The K-factor, which determines how much ratings change after
            each game. Larger values make ratings more responsive.
        initial_rating : int, optional
            The starting Elo rating assigned to every team.
        """

        self.k = k
        self.initial_rating = initial_rating

        # Dictionary storing the current Elo rating for every team.
        self.ratings = {}

        # Stores the Elo history after every game.
        self.history = []


    def initialize_teams(self, games):
        """
        Assign every team in the dataset an initial Elo rating.

        Parameters
        ----------
        games : pandas.DataFrame
            DataFrame containing the regular season game results.
        """

        teams = set(games["HOME_TEAM"]).union(
            set(games["AWAY_TEAM"])
        )

        for team in teams:
            self.ratings[team] = self.initial_rating


    def win_probability(self, team_a, team_b):
        """
        Calculate the expected probability that Team A defeats Team B.

        The probability is calculated using the standard Elo logistic
        function.

        Parameters
        ----------
        team_a : int
            TEAM_ID of the first team.
        team_b : int
            TEAM_ID of the second team.

        Returns
        -------
        float
            Expected probability that Team A wins.
        """

        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]

        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))


    def update_ratings(self, team_a, team_b, winner):
        """
        Update the Elo ratings for two teams after a completed game.

        Ratings increase when a team performs better than expected and
        decrease when a team performs worse than expected.

        Parameters
        ----------
        team_a : int
            TEAM_ID of the first team.
        team_b : int
            TEAM_ID of the second team.
        winner : int
            TEAM_ID of the winning team.
        """

        prob_a = self.win_probability(team_a, team_b)

        actual_a = 1 if winner == team_a else 0

        self.ratings[team_a] += self.k * (actual_a - prob_a)
        self.ratings[team_b] += self.k * ((1 - actual_a) - (1 - prob_a))


    def fit(self, games):
        """
        Fit the Elo model to a season of games.

        Games are processed in chronological order so that team ratings
        evolve naturally throughout the season. After each game, the
        updated ratings are stored in the history list.

        Parameters
        ----------
        games : pandas.DataFrame
            Chronologically ordered regular season games.
        """

        # Initialise ratings if this is the first time fitting.
        if not self.ratings:
            self.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            # Determine the winning team.
            winner = (
                home
                if row["HOME_PTS"] > row["AWAY_PTS"]
                else away
            )

            # Update both teams' Elo ratings.
            self.update_ratings(home, away, winner)

            # Record the updated ratings for later analysis.
            self.history.append({
                "DATE": row["DATE"],
                "GAME_ID": row["GAME_ID"],

                "TEAM": home,
                "ELO": self.ratings[home]
            })

            self.history.append({
                "DATE": row["DATE"],
                "GAME_ID": row["GAME_ID"],

                "TEAM": away,
                "ELO": self.ratings[away]
            })


    def get_ratings(self):
        """
        Return the current Elo ratings for every team.

        Returns
        -------
        dict
            Dictionary mapping team names to their current Elo rating.
        """

        return self.ratings


    def get_rankings(self):
        """
        Return the teams ordered by Elo rating.

        Returns
        -------
        list
            List of (team, rating) tuples sorted from highest to lowest
            Elo rating.
        """

        return sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def get_history(self):
        """
        Return the complete Elo rating history.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing every recorded Elo update throughout
            the season.
        """

        return pd.DataFrame(self.history)

class EloModelMoV(EloModel):
    """
    Model 1: Margin of Victory Elo.

    Extends the baseline EloModel by incorporating point differential
    into rating updates. A blowout win updates ratings more than a
    one-point win, but the relationship is logarithmic rather than
    linear — a 30-point win does not produce 30x the update of a
    1-point win.

    Everything else — initialisation, win probability calculation,
    fitting, history tracking — is inherited unchanged from EloModel.

    The multiplier used is:

        mov_multiplier = log(|point_diff| + 1)

    This is applied as:

        rating_change = K × mov_multiplier × (actual − expected)

    The intuition is that a team which wins comfortably has demonstrated
    more convincingly that they are the stronger side. A narrow win could
    easily have gone the other way; a 25-point win is a clearer signal.

    Using log(diff + 1) rather than the raw differential prevents a
    single extreme blowout from producing an unrealistically large
    rating swing, while still rewarding dominant performances.
    """

    def update_ratings(self, team_a, team_b, winner, point_diff=0):
        """
        Update Elo ratings using a margin-of-victory multiplier.

        Parameters
        ----------
        team_a : int
            TEAM_ID of the first team.
        team_b : int
            TEAM_ID of the second team.
        winner : int
            TEAM_ID of the winning team.
        point_diff : int
            Absolute point differential of the game (always positive).
        """

        prob_a   = self.win_probability(team_a, team_b)
        actual_a = 1 if winner == team_a else 0

        mov_multiplier = math.log(point_diff + 1)

        self.ratings[team_a] += self.k * mov_multiplier * (actual_a - prob_a)
        self.ratings[team_b] += self.k * mov_multiplier * ((1 - actual_a) - (1 - prob_a))


    def fit(self, games):
        """
        Fit the MoV Elo model to a season of games.

        Identical to EloModel.fit() except point_diff is extracted from
        each game row and passed to the overridden update_ratings().

        Parameters
        ----------
        games : pandas.DataFrame
            Chronologically ordered regular season games. Must contain
            HOME_PTS and AWAY_PTS columns.
        """

        if not self.ratings:
            self.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            winner     = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
            point_diff = abs(int(row["HOME_PTS"]) - int(row["AWAY_PTS"]))

            self.update_ratings(home, away, winner, point_diff)

            self.history.append({
                "DATE":    row["DATE"],
                "GAME_ID": row["GAME_ID"],
                "TEAM":    home,
                "ELO":     self.ratings[home]
            })

            self.history.append({
                "DATE":    row["DATE"],
                "GAME_ID": row["GAME_ID"],
                "TEAM":    away,
                "ELO":     self.ratings[away]
            })