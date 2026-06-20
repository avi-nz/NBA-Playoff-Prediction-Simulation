import pandas as pd

class EloModel:


    def __init__(self, k = 20, initial_rating = 1500):
        self.k = k
        self.initial_rating = initial_rating
        self.ratings = {}
        self.history = []


    def initialize_teams(self, games):
        teams = set(games["HOME_TEAM"]).union(
            set(games["AWAY_TEAM"])
        )

        for team in teams:
            self.ratings[team] = self.initial_rating


    def win_probability(self, team_a, team_b):
        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]

        return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))


    def update_ratings(self, team_a, team_b, winner):

        prob_a = self.win_probability(team_a, team_b)

        if winner == team_a:
            error = 1 - prob_a
            self.ratings[team_a] += self.k * error
            self.ratings[team_b] -= self.k * error
        else:
            error = prob_a
            self.ratings[team_a] -= self.k * error
            self.ratings[team_b] += self.k * error


    def fit(self, games):

        if not self.ratings:

            self.initialize_teams(games)

        for _, row in games.iterrows():
            home = row["HOME_TEAM"]
            away = row["AWAY_TEAM"]

            winner = (
                home
                if row["HOME_PTS"] > row["AWAY_PTS"]
                else away
            )

            self.update_ratings(
                home,
                away,
                winner
            )

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
        return self.ratings


    def get_rankings(self):

        return sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def get_history(self):
        return pd.DataFrame(self.history)