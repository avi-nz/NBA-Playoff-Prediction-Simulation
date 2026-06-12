# NBA Playoff Prediction Simulator 

## Loading in the data...

### Attempt 1:

For this project, I am using the NBA API.

My first approach was to use leagueGameLog from the NBA API and load it into a pandas data frame 

```
games = leaguegamelog.LeagueGameLog(
    season='2025-26',
    season_type_all_star='Regular Season'
)

df = games.get_data_frames()[0]
```

This loads in data team wise (this is an important detail which we
will see later).
Because this endpoint is team-centric (as opposed to game game-centric)
it returns one row per team. Therefore, each game will appear twice.
Thus, we must merge them into a single game.

```
games_df = df.sort_values("GAME_DATE")

grouped = []

for game_id, game in games_df.groupby("GAME_ID"):

    if len(game) != 2:
        continue

    team1 = game.iloc[0]
    team2 = game.iloc[1]

    grouped.append({
        "GAME_ID": game_id,
        "DATE": team1["GAME_DATE"],

        "TEAM_A": team1["TEAM_NAME"],
        "TEAM_B": team2["TEAM_NAME"],

        "PTS_A": team1["PTS"],
        "PTS_B": team2["PTS"]
    })

games = pd.DataFrame(grouped)
games = games.sort_values("DATE")
```

We can do this my first sorting the games by when they were played so the teams that play
each other on the same night will be next to each other.
Then we need make sure that there are two teams playing on each given night. If not then skip that date.
Assign one team to team A and the other to Team B and also store other important information such as
the game_ID the team names and also what was the score of each team so we can see who won the game.

```
         GAME_ID        DATE  ... TEAM_A_PTS TEAM_B_PTS
0     0022500001  2025-10-21  ...        124        125
1     0022500002  2025-10-21  ...        119        109
2     0022500003  2025-10-22  ...        111        119
3     0022500004  2025-10-22  ...         92        125
4     0022500005  2025-10-23  ...        135        141
...          ...         ...  ...        ...        ...
1225  0022501226  2025-12-15  ...        121        103
1226  0022501227  2025-12-15  ...         96        106
1227  0022501228  2025-12-14  ...        114        116
1228  0022501229  2025-12-13  ...        120        132
1229  0022501230  2025-12-13  ...        109        111
```

And, as you can see by the output, this worked!

We now use simple maths to determine who won each game by seeing which team had the higher score.

However, there was one issue. I did not know which team was the home team and which was the away team.
This is not currently important to me at this stage, however I plan on adding another layers/iterations of this 
simulation one of which includes seeing if home court advantage makes a difference (and obviously for that I would need
to know who the home team is). Thus, for the sake of future proofing, I wanted to see if I can get the data to tell us 
who is the home team and who is the away team.

a solution that I thought of was to use some sort of phrasing system.
The NBA uses @ symbol for when a team is 'on the road' i.e they are the away team but for home teams they use v.s.

For example...

OKC @ HOU - This would mean that OKC are the away team and they are playing HOU (who are the home team)
MIN v.s SAS - THis would mean that the MIN are the home team and they are facing SAS (who are the away team)

Therefore, I printed out the matchup to the terminal so I could see the format, and this is what I found...
```
-------------------------------------------------- 
TEAM_NAME MATCHUP 
770 Dallas Mavericks DAL @ UTA 
772 Utah Jazz UTA vs. DAL 
-------------------------------------------------- 
TEAM_NAME MATCHUP 
771 Houston Rockets HOU @ DEN 
764 Denver Nuggets DEN vs. HOU 
-------------------------------------------------- 
TEAM_NAME MATCHUP  
773 emphis Grizzlies MEM @ LAC 
767 LA Clippers LAC vs. MEM  
-------------------------------------------------- 
TEAM_NAME MATCHUP 
747 Orlando Magic ORL @ NYK 
746 New York Knicks NYK @ ORL 
-------------------------------------------------- 
TEAM_NAME MATCHUP 
745 Oklahoma City Thunder OKC @ SAS 
744 San Antonio Spurs SAS @ OKC 
--------------------------------------------------
```

(NOTE: This is only a select sample size)

As you can see most of the data was formatted as expected. However, if we look at the last two, we can see that both
use the '@' symbol which does not make sense because both team cannot be at home.

After some messing around I decided to no longer use this data set and move onto another because it became apparent 
that figuring out who was the home and away team with this data set would be more challenging that what it was worth.

This issue with this data set is that it is **team-centric** meaning it shows the result of each team (which is why we 
get double ups for each game). What will be better for we are trying to achieve is a game-centric data set meaning the 
data shows the result of each game.

#### Team-centric data set:
| GAME_ID | TEAM_NAME | MATCHUP     | PTS |
| ------- | --------- | ----------- | --- |
| 001     | Lakers    | LAL vs. GSW | 112 |
| 001     | Warriors  | GSW @ LAL   | 108 |


#### Game-centric data set:
| GAME_ID | HOME_TEAM | AWAY_TEAM | HOME_PTS | AWAY_PTS |
| ------- | --------- | --------- | -------- | -------- |
| 001     | Lakers    | Warriors  | 112      | 108      |


### Attempt 2:
