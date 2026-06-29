import random

class PlayoffSimulator:
    """
    Simulates the NBA playoffs using an Elo model.
    """

    def __init__(self, elo_model):
        """
        Initialise the playoff simulator.

        Parameters
        ----------
        elo_model : EloModel
            Trained Elo model containing the final regular-season ratings.
        """
        self.elo = elo_model


    def simulate_game(self, team_a_id, team_b):
        """
        Simulate a single game.

        Returns
        -------
        str
            Winning team.
        """

        prob = self.elo.win_probability(team_a_id, team_b)

        if random.random() < prob:
            return team_a_id

        return team_b

    def simulate_series(self, team_a, team_b):
        """
        Simulate a best-of-seven playoff series.

        Parameters
        ----------
        team_a : str
        team_b : str

        Returns
        -------
        dict
            Information about the completed series.
        """

        wins = {
            team_a: 0,
            team_b: 0
        }

        games_played = 0

        while wins[team_a] < 4 and wins[team_b] < 4:
            winner = self.simulate_game(team_a, team_b)

            wins[winner] += 1
            games_played += 1

        if wins[team_a] == 4:
            winner = team_a
            loser = team_b
        else:
            winner = team_b
            loser = team_a

        return {
            "winner": winner,
            "loser": loser,
            "games": games_played,
            "wins": wins.copy()
        }


    def simulate_conference(self, teams):
        """
        Simulate an entire conference playoff bracket.

        Parameters
        ----------
        teams : list
            Teams ordered by playoff seed (1-8).

        Returns
        -------
        dict
            Complete conference results.
        """

        # First Round
        first_round = [
            self.simulate_series(teams[0], teams[7]),  # 1 vs 8
            self.simulate_series(teams[3], teams[4]),  # 4 vs 5
            self.simulate_series(teams[1], teams[6]),  # 2 vs 7
            self.simulate_series(teams[2], teams[5])  # 3 vs 6
        ]

        # Conference Semifinals
        semifinals = [
            self.simulate_series(
                first_round[0]["winner"],
                first_round[1]["winner"]
            ),

            self.simulate_series(
                first_round[2]["winner"],
                first_round[3]["winner"]
            )
        ]

        # Conference Finals
        conference_finals = self.simulate_series(
            semifinals[0]["winner"],
            semifinals[1]["winner"]
        )

        return {
            "first_round": first_round,
            "semifinals": semifinals,
            "conference_finals": conference_finals,
            "winner": conference_finals["winner"]
        }


    def simulate_playoffs(self, east, west):
        """
        Simulate the complete NBA playoffs.

        Parameters
        ----------
        east : list
            Eastern Conference playoff teams ordered by seed (1-8).

        west : list
            Western Conference playoff teams ordered by seed (1-8).

        Returns
        -------
        dict
            Complete playoff results.
        """

        east_results = self.simulate_conference(east)
        west_results = self.simulate_conference(west)

        finals = self.simulate_series(
            east_results["winner"],
            west_results["winner"]
        )

        return {
            "east": east_results,
            "west": west_results,
            "finals": finals,
            "champion": finals["winner"]
        }


    def simulate_many(self, east, west, n_simulations=10000):
        """
        Run many playoff simulations.

        Parameters
        ----------
        east : list
        west : list
        n_simulations : int

        Returns
        -------
        dict
            Championship probabilities.
        """

        champions = {}

        for _ in range(n_simulations):
            results = self.simulate_playoffs(east, west)

            champion = results["champion"]

            champions[champion] = champions.get(champion, 0) + 1

        for team in champions:
            champions[team] /= n_simulations

        return champions