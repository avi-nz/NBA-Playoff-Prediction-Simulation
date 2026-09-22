"""
injury_loader.py

Builds per-team player availability profiles for the playoff simulator.

For each playoff team:
1. Fetches advanced player statistics.
2. Selects the top 5 players by PIE.
3. Estimates each player's absence rate from games played
   relative to the team's maximum player GP.
4. Computes each player's PIE share among the top 5 players.

The resulting profiles are passed to EloModelInjury.
"""

import time

from nba_api.stats.endpoints import leaguedashplayerstats

from src.data.teams import TEAM_ID_TO_NAME


def get_injury_profiles(season, team_ids, n_players=5):
    """
    Build an injury/availability profile for each playoff team.

    Parameters
    ----------
    season : str
        NBA season string, e.g. "2024-25".

    team_ids : list[int]
        TEAM_IDs of the 16 playoff teams.

    n_players : int
        Number of top players to track per team.

    Returns
    -------
    dict
        {
            team_id: [
                {
                    "player_id": int,
                    "name": str,
                    "ws_fraction": float,
                    "injury_rate": float,
                }
            ]
        }
    """

    print("    Fetching advanced player stats...")

    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        measure_type_detailed_defense="Advanced"
    ).get_data_frames()[0]

    time.sleep(1)

    # Filter to playoff teams only.
    stats = stats[
        stats["TEAM_ID"].isin(team_ids)
    ].copy()

    profiles = {}

    for team_id in team_ids:

        team_stats = stats[
            stats["TEAM_ID"] == team_id
        ].copy()

        if team_stats.empty:
            print(
                f"    WARNING: no stats found for "
                f"{TEAM_ID_TO_NAME.get(team_id, team_id)}"
            )

            profiles[team_id] = []
            continue

        # Estimate the number of team games from the
        # maximum GP among players.
        team_total_games = int(team_stats["GP"].max())

        if team_total_games == 0:
            profiles[team_id] = []
            continue

        # Exclude traded players — anyone who played fewer than half
        # the team's games was likely acquired mid-season. Their low GP
        # reflects time with another team, not injury history, which
        # would produce wildly inflated injury rates.
        min_games = team_total_games * 0.5
        eligible = team_stats[team_stats["GP"] >= min_games].copy()

        if eligible.empty:
            # Fallback: relax threshold to 25% if nobody qualifies
            eligible = team_stats[
                team_stats["GP"] >= team_total_games * 0.25
            ].copy()

        # Select the team's most impactful players by PIE.
        top_players = (
            eligible
            .sort_values("PIE", ascending=False)
            .head(n_players)
        )

        # Total PIE of tracked players.
        total_pie = top_players["PIE"].sum()

        if total_pie <= 0:
            total_pie = 1.0

        players = []

        for _, row in top_players.iterrows():

            games_played = int(row["GP"])

            # Injury rate: fraction of team games this player missed.
            # Because we filtered to players with the team for at least
            # half the season, this now reflects genuine absences
            # (injury, rest) rather than mid-season trades.
            injury_rate = max(
                0.0,
                (team_total_games - games_played) / team_total_games
            )

            players.append({
                "player_id": int(row["PLAYER_ID"]),
                "name": row["PLAYER_NAME"],
                "ws_fraction": float(row["PIE"]) / total_pie,
                "injury_rate": injury_rate,
            })

        profiles[team_id] = players

    return profiles


def print_injury_profiles(profiles):
    """
    Pretty-print injury profiles for all playoff teams.
    """

    for team_id, players in profiles.items():

        name = TEAM_ID_TO_NAME.get(
            team_id,
            str(team_id)
        )

        print(f"\n  {name}")
        print(
            f"  {'PLAYER':<28} "
            f"{'PIE SHARE':>10}  "
            f"{'INJURY RATE':>12}"
        )
        print(f"  {'-' * 54}")

        for player in players:

            print(
                f"  {player['name']:<28} "
                f"{player['ws_fraction'] * 100:>9.1f}%  "
                f"{player['injury_rate'] * 100:>11.1f}%"
            )
