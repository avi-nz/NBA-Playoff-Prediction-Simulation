from nba_api.stats.static import teams

NBA_TEAMS = teams.get_teams()

TEAM_NAME_TO_ID = {
    t["full_name"].strip(): t["id"]
    for t in NBA_TEAMS
}

TEAM_ABBREV_TO_ID = {
    t["abbreviation"]: t["id"]
    for t in NBA_TEAMS
}