"""
elo.py

Implements a basic Elo rating system used to estimate NBA team strength.

The model processes regular season games chronologically, updates team
ratings after every match, and stores a complete history of Elo ratings
for later analysis and playoff simulation.
"""

import pandas as pd
import math


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
    Model 1: Margin of Victory Elo with tunable parameters.

    Extends the baseline EloModel by incorporating point differential
    into rating updates via a parameterised MOV multiplier:

        mov_multiplier = (point_diff + a)^b / (c + d * elo_diff)

    where elo_diff is the winner's pregame Elo minus the loser's.

    The four parameters (a, b, c, d) default to FiveThirtyEight's
    empirically-fitted values but can be overridden — for example, by
    tune_mov.py which searches for the values that minimise game-level
    Brier score on historical NBA seasons.

    Parameters
    ----------
    k : int
        K-factor. Controls overall rating sensitivity.
    initial_rating : int
        Starting Elo rating for every team.
    a : float
        Shift applied to the margin before exponentiation. Prevents
        very close games from producing near-zero multipliers.
    b : float
        Exponent controlling the shape of diminishing returns.
    c : float
        Base denominator value. Controls the overall scale of the
        expectation correction.
    d : float
        Scales how much the pregame Elo difference reduces or
        increases the multiplier for favourites and underdogs.
    """

    def __init__(self, k=20, initial_rating=1500, a=0.0000, b=0.6967, c=4.1340, d=0.0006):
        super().__init__(k, initial_rating)
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def update_ratings(self, team_a, team_b, winner, point_diff=0):
        """
        Update Elo ratings using the parameterised MOV multiplier.

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

        prob_a = self.win_probability(team_a, team_b)
        actual_a = 1 if winner == team_a else 0

        loser = team_b if winner == team_a else team_a
        elo_diff = self.ratings[winner] - self.ratings[loser]

        mov_multiplier = (point_diff + self.a) ** self.b / (self.c + self.d * elo_diff)

        self.ratings[team_a] += self.k * mov_multiplier * (actual_a - prob_a)
        self.ratings[team_b] += self.k * mov_multiplier * ((1 - actual_a) - (1 - prob_a))


    def fit(self, games):
        """
        Fit the MoV Elo model to a season of games.

        Identical to EloModel.fit() except point_diff is extracted and
        passed to the overridden update_ratings().

        Parameters
        ----------
        games : pandas.DataFrame
            Chronologically ordered regular season games.
        """

        if not self.ratings:
            self.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            winner = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
            point_diff = abs(int(row["HOME_PTS"]) - int(row["AWAY_PTS"]))

            self.update_ratings(home, away, winner, point_diff)

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


class EloModelHCA(EloModel):
    """
    Model 2: Home Court Advantage Elo.

    Extends the baseline EloModel by adding a fixed Elo bonus to the
    home team before calculating win probability. The home team is
    treated as if they are `home_advantage` Elo points stronger than
    they actually are for that game only — ratings themselves are never
    permanently changed by the bonus.

    Neutral site games (NBA Cup) receive no home court bonus since
    neither team has an actual home court.

    Parameters
    ----------
    home_advantage : float
        Elo points added to the home team's rating before computing
        win probability and rating updates. Defaults to 100, a common
        starting point in Elo literature. Can be tuned via tune_hca.py.
    """

    def __init__(self, k=20, initial_rating=1500, home_advantage=100):
        super().__init__(k, initial_rating)
        self.home_advantage = home_advantage

    def win_probability(self, team_a, team_b, home_team=None):
        """
        Calculate the expected probability that Team A defeats Team B,
        optionally applying a home court bonus.

        Parameters
        ----------
        team_a : int
            TEAM_ID of the first team.
        team_b : int
            TEAM_ID of the second team.
        home_team : int or None
            TEAM_ID of the home team. If None (neutral site), no bonus
            is applied. If team_a, team_a gets the bonus. If team_b,
            team_b gets the bonus.

        Returns
        -------
        float
            Expected probability that Team A wins.
        """

        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]

        if home_team == team_a:
            rating_a += self.home_advantage
        elif home_team == team_b:
            rating_b += self.home_advantage

        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))

    def update_ratings(self, team_a, team_b, winner, home_team=None):
        """
        Update Elo ratings using home court adjusted probabilities.

        Parameters
        ----------
        team_a : int
            TEAM_ID of the first team.
        team_b : int
            TEAM_ID of the second team.
        winner : int
            TEAM_ID of the winning team.
        home_team : int or None
            TEAM_ID of the home team. None for neutral site games.
        """

        prob_a = self.win_probability(team_a, team_b, home_team)
        actual_a = 1 if winner == team_a else 0

        self.ratings[team_a] += self.k * (actual_a - prob_a)
        self.ratings[team_b] += self.k * ((1 - actual_a) - (1 - prob_a))

    def fit(self, games):
        """
        Fit the HCA Elo model to a season of games.

        HOME_AWAY games pass the home team to update_ratings so the
        bonus is applied. NEUTRAL site games pass None so no bonus
        is applied.

        Parameters
        ----------
        games : pandas.DataFrame
            Chronologically ordered regular season games. Must contain
            a SITE_TYPE column with values "HOME_AWAY" or "NEUTRAL".
        """

        if not self.ratings:
            self.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            winner = home if row["HOME_PTS"] > row["AWAY_PTS"] else away

            home_team = home if row["SITE_TYPE"] == "HOME_AWAY" else None

            self.update_ratings(home, away, winner, home_team)

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
