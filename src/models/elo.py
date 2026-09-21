import pandas as pd

"""
elo.py

Implements a family of Elo rating models for NBA team strength estimation.

All models share a single base class (EloModel) which owns the core
algorithm: storing ratings, computing win probability, updating after
each game, and recording history.

Subclasses override only the methods that differ:

    EloModel          — baseline Elo, no adjustments
    EloModelMoV       — margin-of-victory multiplier
    EloModelHCA       — home court advantage bonus

The fit() method lives only in the base class. Subclasses never
duplicate it — they only change what happens inside update_ratings().
"""

# ---------------------------------------------------------------------------

class EloModel:
    """
    Baseline Elo rating system (Model 0).

    Each team begins with the same initial rating and is updated after
    every game based on the expected and actual outcome.
    """

    def __init__(self, k=20, initial_rating=1500):
        """
        Initialise the Elo model.

        Parameters
        ----------
        k : int
            K-factor. Controls how much ratings change after each game.
        initial_rating : int
            Starting Elo rating assigned to every team.
        """

        self.k              = k
        self.initial_rating = initial_rating
        self.ratings        = {}
        self.history        = []


    def initialize_teams(self, games):
        """
        Assign every team in the dataset an initial Elo rating.

        Parameters
        ----------
        games : pandas.DataFrame
        """

        teams = set(games["HOME_TEAM"]).union(set(games["AWAY_TEAM"]))

        for team in teams:
            self.ratings[team] = self.initial_rating


    def win_probability(self, team_a, team_b, home_team=None):
        """
        Expected probability that Team A defeats Team B.

        The base model ignores home_team. Subclasses that implement
        home court advantage override this method to apply a bonus.

        Parameters
        ----------
        team_a : int
        team_b : int
        home_team : int or None
            Accepted but ignored by the base model. Present so the
            playoff simulator can always pass home_team without needing
            to know which model it's using.

        Returns
        -------
        float
        """

        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]

        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))


    def update_ratings(self, row):
        """
        Update ratings for both teams after a single game.

        Subclasses override this method to add features such as margin
        of victory or home court advantage. The base model uses only
        the binary win/loss outcome.

        Parameters
        ----------
        row : pandas.Series
            A single row from the games DataFrame. Expected columns:
            HOME_TEAM, AWAY_TEAM, HOME_PTS, AWAY_PTS.
        """

        home   = row["HOME_TEAM"]
        away   = row["AWAY_TEAM"]
        winner = home if row["HOME_PTS"] > row["AWAY_PTS"] else away

        prob_a   = self.win_probability(home, away)
        actual_a = 1 if winner == home else 0

        self.ratings[home] += self.k * (actual_a - prob_a)
        self.ratings[away] += self.k * ((1 - actual_a) - (1 - prob_a))


    def fit(self, games):
        """
        Fit the Elo model to a season of games.

        Processes games chronologically. After each game calls
        self.update_ratings(row) — which subclasses override — then
        records the updated ratings in history.

        This method is defined once here and never duplicated in
        subclasses.

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

            self.update_ratings(row)

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


    def get_ratings(self):
        return self.ratings


    def get_rankings(self):
        return sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)


    def get_history(self):
        return pd.DataFrame(self.history)


# ---------------------------------------------------------------------------

class EloModelMoV(EloModel):
    """
    Model 1: Margin of Victory Elo.

    Extends EloModel with a parameterised MOV multiplier:

        (point_diff + a)^b / (c + d * elo_diff)

    Only update_ratings() is overridden. fit() is inherited.
    """

    def __init__(self, k=20, initial_rating=1500, a=3, b=0.8, c=7.5, d=0.006):
        super().__init__(k, initial_rating)
        self.a = a
        self.b = b
        self.c = c
        self.d = d


    def update_ratings(self, row):
        """
        Update ratings using the margin-of-victory multiplier.

        Parameters
        ----------
        row : pandas.Series
        """

        home       = row["HOME_TEAM"]
        away       = row["AWAY_TEAM"]
        winner     = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
        loser      = away if winner == home else home
        point_diff = abs(int(row["HOME_PTS"]) - int(row["AWAY_PTS"]))

        prob_a   = self.win_probability(home, away)
        actual_a = 1 if winner == home else 0

        elo_diff       = self.ratings[winner] - self.ratings[loser]
        mov_multiplier = (point_diff + self.a) ** self.b / (self.c + self.d * elo_diff)

        self.ratings[home] += self.k * mov_multiplier * (actual_a - prob_a)
        self.ratings[away] += self.k * mov_multiplier * ((1 - actual_a) - (1 - prob_a))


# ---------------------------------------------------------------------------

class EloModelHCA(EloModel):
    """
    Model 2: Home Court Advantage Elo.

    Extends EloModel by adding a fixed Elo bonus to the home team
    before computing win probability. The bonus affects probability
    calculations and rating updates but never permanently modifies
    stored ratings.

    Neutral site games (NBA Cup) receive no bonus.

    Only win_probability() and update_ratings() are overridden.
    fit() is inherited.

    Parameters
    ----------
    home_advantage : float
        Elo points added to the home team's effective rating.
        Defaults to 100. Tune with tune_hca.py.
    """

    def __init__(self, k=20, initial_rating=1500, home_advantage=100):
        super().__init__(k, initial_rating)
        self.home_advantage = home_advantage


    def win_probability(self, team_a, team_b, home_team=None):
        """
        Win probability with optional home court bonus.

        Parameters
        ----------
        team_a : int
        team_b : int
        home_team : int or None
            TEAM_ID of the home team. None for neutral site.
        """

        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]

        if home_team == team_a:
            rating_a += self.home_advantage
        elif home_team == team_b:
            rating_b += self.home_advantage

        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))


    def update_ratings(self, row):
        """
        Update ratings with home court adjusted probabilities.

        Parameters
        ----------
        row : pandas.Series
            Must include SITE_TYPE column ("HOME_AWAY" or "NEUTRAL").
        """

        home      = row["HOME_TEAM"]
        away      = row["AWAY_TEAM"]
        winner    = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
        home_team = home if row["SITE_TYPE"] == "HOME_AWAY" else None

        prob_a   = self.win_probability(home, away, home_team)
        actual_a = 1 if winner == home else 0

        self.ratings[home] += self.k * (actual_a - prob_a)
        self.ratings[away] += self.k * ((1 - actual_a) - (1 - prob_a))

class EloModelDynamicHCA(EloModel):
    """Model 2b: Dynamic Home Court Advantage Elo."""

    def __init__(self, k=20, initial_rating=1500,
                 initial_home_advantage=60, k_hca=5):
        super().__init__(k, initial_rating)
        self.initial_home_advantage = initial_home_advantage
        self.k_hca           = k_hca
        self.home_advantages = {}

    def initialize_teams(self, games):
        super().initialize_teams(games)
        teams = set(games["HOME_TEAM"]).union(set(games["AWAY_TEAM"]))
        self.home_advantages = {t: self.initial_home_advantage for t in teams}

    def win_probability(self, team_a, team_b, home_team=None):
        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]
        if home_team == team_a:
            rating_a += self.home_advantages.get(team_a, self.initial_home_advantage)
        elif home_team == team_b:
            rating_b += self.home_advantages.get(team_b, self.initial_home_advantage)
        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))

    def update_ratings(self, row):
        super().update_ratings(row)
        home      = row["HOME_TEAM"]
        home_team = home if row["SITE_TYPE"] == "HOME_AWAY" else None
        if home_team is not None:
            away     = row["AWAY_TEAM"]
            winner   = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
            prob_a   = self.win_probability(home, away, home_team)
            actual_a = 1 if winner == home else 0
            self.home_advantages[home] += self.k_hca * (actual_a - prob_a)


class EloModelRecentForm(EloModel):
    """Model 3: Recent Form Elo — progressive K-factor."""

    def __init__(self, k=20, initial_rating=1500,
                 k_start_mult=0.5, k_end_mult=1.5):
        super().__init__(k, initial_rating)
        self.k_start_mult = k_start_mult
        self.k_end_mult   = k_end_mult
        self.game_count   = 0
        self.total_games  = 0

    def initialize_teams(self, games):
        super().initialize_teams(games)
        self.game_count  = 0
        self.total_games = len(games)

    def update_ratings(self, row):
        self.game_count += 1
        progress     = self.game_count / self.total_games
        k_multiplier = self.k_start_mult + (self.k_end_mult - self.k_start_mult) * progress
        k_effective  = self.k * k_multiplier
        home      = row["HOME_TEAM"]
        away      = row["AWAY_TEAM"]
        winner    = home if row["HOME_PTS"] > row["AWAY_PTS"] else away
        home_team = home if row["SITE_TYPE"] == "HOME_AWAY" else None
        prob_a   = self.win_probability(home, away, home_team)
        actual_a = 1 if winner == home else 0
        self.ratings[home] += k_effective * (actual_a - prob_a)
        self.ratings[away] += k_effective * ((1 - actual_a) - (1 - prob_a))


class EloModelBayesian(EloModel):
    """Model 5: Bayesian Team Strength — rating distributions."""

    def get_rating_stds(self):
        history_df = pd.DataFrame(self.history)
        return history_df.groupby("TEAM")["ELO"].std().to_dict()


class EloModelInjury(EloModel):
    """
    Model 6: Injury-Adjusted Elo.

    Before each simulated game, rolls each team's top 5 players
    against their historical injury rate. Injured players reduce
    the team's effective Elo by their PIE share × star_impact.

    Parameters
    ----------
    star_impact : float
        Total Elo drop if all top 5 players are unavailable.
    injury_profiles : dict
        {team_id: [{"name", "ws_fraction", "injury_rate"}]}
        Built by injury_loader.get_injury_profiles().
    """

    def __init__(self, k=20, initial_rating=1500,
                 star_impact=500, injury_profiles=None):
        super().__init__(k, initial_rating)
        self.star_impact     = star_impact
        self.injury_profiles = injury_profiles or {}
        self.injury_log      = {}   # {player_name: total injury count across all sim games}


    def _elo_penalty(self, team_id):
        """
        Roll injuries for a team and return the total Elo penalty.
        Records any injuries into self.injury_log for post-sim reporting.
        """

        import random

        players = self.injury_profiles.get(team_id, [])
        penalty = 0.0

        for player in players:
            if random.random() < player["injury_rate"]:
                penalty += player["ws_fraction"] * self.star_impact
                name = player["name"]
                self.injury_log[name] = self.injury_log.get(name, 0) + 1

        return penalty


    def reset_injury_log(self):
        """Clear the injury log before a new simulation run."""
        self.injury_log = {}


    def win_probability(self, team_a, team_b, home_team=None):
        penalty_a = self._elo_penalty(team_a)
        penalty_b = self._elo_penalty(team_b)
        rating_a  = self.ratings[team_a] - penalty_a
        rating_b  = self.ratings[team_b] - penalty_b
        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))

