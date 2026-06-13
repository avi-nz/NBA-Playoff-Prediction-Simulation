# NBA Playoff Prediction Simulator 
***

## Loading in the data...

### Attempt 1:

For this project, I am using the NBA API.

My first approach was to use leagueGameLog from the NBA API and load it into a pandas data frame 

```python
games = leaguegamelog.LeagueGameLog(
    season='2025-26',
    season_type_all_star='Regular Season'
)

df = games.get_data_frames()[0]
```

This loads in data team-wise (this is an important detail, which we
will see later).
Because this endpoint is team-centric (as opposed to game-centric)
It returns one row per team. Therefore, each game will appear twice.
Thus, we must merge them into a single game.

```python
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

We can do this my first sorting the games by when they were played, so the teams that play
each other on the same night will be next to each other.
Then we need to make sure there are two teams playing each night. If not, then skip that date.
Assign one team to Team A and the other to Team B, and also store other important information such as
the game_ID, the team names, and also what was the score of each team so we can see who won the game.

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

We now use simple maths to determine who won each game by comparing the teams' scores.

However, there was one issue. I did not know which team was the home team and which was the away team.
This is not currently important to me at this stage; however, I plan on adding another layers/iterations of this 
simulation, one of which includes seeing if home court advantage makes a difference (and obviously, for that, I would need
to know who the home team is). Thus, for the sake of future proofing, I wanted to see if I could get the data to tell us 
who is the home team and who is the away team.

A solution I considered was to use some sort of phrasing system.
The NBA uses @ symbol for when a team is 'on the road' i.e they are the away team but for home teams they use v.s.

For example...

OKC @ HOU - This would mean that OKC are the away team and they are playing HOU (who are the home team)
MIN v.s SAS - This would mean that the MIN are the home team and they are facing SAS (who are the away team)

Therefore, I printed the matchup to the terminal to see the format, and this is what I found...
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

As you can see, most of the data was formatted as expected. However, if we look at the last two, we can see that both
Use the '@' symbol, which does not make sense because both teams cannot be at home.

After some messing around, I decided to no longer use this data set and move on to another because it became apparent 
Figuring out who was the home and away team with this data set would be more challenging than it was worth.

This issue with this data set is that it is **team-centric**, meaning it shows the result of each team (which is why we 
get double-ups for each game). What will be better for we are trying to achieve is a game-centric data set, meaning the 
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
After some research I have decided to pivot away from the Game-centric data set and go back to the Team-centric data
set 😂

#### Why go back to Team-Centric before even trying Game-centric?
Initially, I considered switching to a game-centric endpoint such as ```ScoreboardV2``` because it directly provides game-level 
information, including home and away teams. This would eliminate the need to merge team records together and would make 
home-court analysis much easier.

However, after investigating the API further, I realised that using a game-centric approach would significantly 
increase the number of API requests required.

The ```LeagueGameLog``` endpoint allows an entire season's worth of games to be downloaded in a single request. Although the 
data is team-centric and each game appears twice, all regular season results are immediately available and can be 
cleaned with a relatively small amount of preprocessing.

By contrast, ```ScoreboardV2``` is designed around individual dates. To reconstruct an entire season, 
I would need to query the endpoint separately for every day of the NBA calendar and then combine all of the returned 
data. A full NBA season spans roughly six months, meaning well over 170 API requests would be required just to collect 
the same information that ```LeagueGameLog``` provides in a single call.

In addition to being slower, this approach introduces several disadvantages:

Increased runtime due to hundreds of API calls.
Greater likelihood of request failures or rate limiting.
More complex data collection and storage pipelines.
Additional code required to merge and validate data from multiple responses.

Because my primary objective is to build an Elo-based playoff prediction model rather than a data collection system, 
the simplicity of ```LeagueGameLog``` outweighs the inconvenience of having to identify home and away teams manually.

As I will discuss later on, I discovered that the apparent matchup inconsistencies were actually neutral-site NBA Cup 
games rather than data errors, the main reason for abandoning the team-centric dataset disappeared

#### What about the issue of figuring out which team was at Home vs Away?
Turns out that this was not a bug, but a feature 😂😂😂

```python
bad_games = []

for game_id, game in games_df.groupby("GAME_ID"):

    home = game[game["MATCHUP"].str.contains("vs.", regex=False)]
    away = game[game["MATCHUP"].str.contains("@", regex=False)]

    if len(home) != 1 or len(away) != 1:
        bad_games.append(game_id)
        continue
```
I went through and stored all the 'bad' games in a list to see how many there were and also to see which games were 'bad'.
This is what I found...
```
Bad Game ID: 0022500147
            TEAM_NAME    MATCHUP
168  Dallas Mavericks  DAL @ DET
165   Detroit Pistons  DET @ DAL
--------------------------------------------------

Bad Game ID: 0022500578
              TEAM_NAME    MATCHUP
1209  Memphis Grizzlies  MEM @ ORL
1207      Orlando Magic  ORL @ MEM
--------------------------------------------------

Bad Game ID: 0022500602
              TEAM_NAME    MATCHUP
1261  Memphis Grizzlies  MEM @ ORL
1256      Orlando Magic  ORL @ MEM
--------------------------------------------------

Bad Game ID: 0022501229
           TEAM_NAME    MATCHUP
747    Orlando Magic  ORL @ NYK
746  New York Knicks  NYK @ ORL
--------------------------------------------------

Bad Game ID: 0022501230
                 TEAM_NAME    MATCHUP
745  Oklahoma City Thunder  OKC @ SAS
744      San Antonio Spurs  SAS @ OKC
--------------------------------------------------

Bad games found: 5
```

In the 2025-26 season there were 5 'bad' games. Because we have the game ID I searched these games on google and turns 
out these games are apart of the NBA Cup. Which is a mid-season tournament, where the final games are held in Las Vegas
which is a neutral site, meaning there is no home or away team. Thus, the matchup does not follow the conventional format.

This is what I mean when I say that this turns out to be a feature not a bug.

So therefore there is nothing wrong with this data set and we can continue to use it and all we have to do it take into 
account that these games are played on a neutral site.

As a result, I decided to continue using ```LeagueGameLog``` as the project's primary data source.


