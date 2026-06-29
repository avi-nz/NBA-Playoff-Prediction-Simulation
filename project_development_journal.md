# NBA Playoff Prediction Simulator Project Development Document
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
out these games were apart of the NBA Cup. Which is a mid-season tournament, where the final games are held in Las Vegas
which is a neutral site, meaning there is no home or away team. Thus, the matchup does not follow the conventional format.

This is what I mean when I say that this turns out to be a feature not a bug.

So therefore there is nothing wrong with this data set and we can continue to use it and all we have to do it take into 
account that these games are played on a neutral site.

As a result, I decided to continue using ```LeagueGameLog``` as the project's primary data source.

***
Now that we have figured out that the 'bad' games were apart of the NBA Cup, we can add some code to detect these games 
so we can label them appropriately.

I added a list ```neutral_games = []``` so I can keep track of the amount of neutral games.

```python
# Case 2: neutral site game (NBA Cup / special games)
# len of away = 2 cause both teams are marked as away when there is a neutral site.
elif len(home) == 0 and len(away) == 2:

    # in neutral games, BOTH rows usually have "@"
    # so we just take both teams safely
    team_a = game.iloc[0]
    team_b = game.iloc[1]

    neutral_games.append(game_id)

    grouped_games.append({
        "GAME_ID": game_id,
        "DATE": team_a["GAME_DATE"],

        "HOME_TEAM": "TEAM_A",
        "AWAY_TEAM": "TEAM_B",

        "HOME_PTS": team_a["PTS"],
        "AWAY_PTS": team_b["PTS"],

        "SITE_TYPE": "NEUTRAL"
            })
```
I then add an if statement which checks if the length of the away teams is equal 2 and also the length of the home teams 
is 1. The reason why this works is because the data shows...
```
DAL @ DET
DET @ DAL
```
Meaning both teams are marked as 'away' so therefore...
```python
home = game[game["MATCHUP"].str.contains("vs.", regex=False)]
away = game[game["MATCHUP"].str.contains("@", regex=False)]
```
Gives...
```python
len(home) == 0
len(away) == 2
```

I then also added a tag ```SITE_TYPE```
```python
SITE_TYPE = "HOME_AWAY" | "NEUTRAL"
```
To show if a game is a traditional home/away game or if it is played on a neutral site.

This additional variable allows later versions of the Elo model to distinguish between traditional home-court games 
and neutral-site games. Home-court advantage can therefore be incorporated into the rating updates while ensuring that 
neutral-site games receive no such adjustment.

At this point, the data preprocessing pipeline was complete. Every regular season game had been converted into a 
single game-level observation containing the competing teams, the final scores, the game date and the site type 
(home/away or neutral). This cleaned dataset forms the input to the Elo rating system described in the next section.

## Building the Elo Rating System

With a reliable game dataset available, the next stage of the project was to develop an Elo rating system capable of 
estimating team strength throughout the season. Elo ratings provide a simple yet effective method for updating a team's 
estimated ability after every game based on the expected and actual outcome. These ratings will later form the 
foundation of the playoff prediction simulator.

### Why Elo?
The Elo rating system was originally developed by Arpad Elo for ranking chess players, but has since become widely used 
In many sports, due to its simplicity and effectiveness.

The main advantage of Elo is that it provides a dynamic measure of team strength. Instead of relying solely on wins 
and losses, the rating adjusts based on how expected the result was. For example, if a highly rated team defeats a 
much weaker team, only a small rating adjustment is made because the result was expected. Conversely, if an underdog 
defeats a highly rated opponent, both teams receive a much larger rating adjustment.

This continual updating process allows the ratings to evolve throughout the season as 
teams improve or decline in performance. These ratings can then be used to estimate the probability of 
future game outcomes, making Elo an ideal foundation for a Monte Carlo playoff simulator.

### Expected Win Probability
The Elo rating system does not directly compare two teams' ratings. Instead, it converts the difference between their 
ratings into a predicted probability of winning.

This conversion is performed using a sigmoid function. A sigmoid function is a mathematical function that 
maps any real number onto a value between 0 and 1, making it ideal for representing probabilities.

<img width="1217" height="960" alt="Screenshot 2026-06-29 at 15 55 02" src="https://github.com/user-attachments/assets/85df86c0-52fa-4f8a-9a21-3b36b0e3b0ec" />

The Elo system uses the following sigmoid equation:

$$
P(A)=\frac{1}{1+10^{-(R_A-R_B)/400}}
$$

where:
* $R_A$ is Team A's current Elo rating.
* $R_B$ is Team B's current Elo rating.

The key advantage of using a sigmoid function is that it produces sensible probabilities regardless of how large or 
small the rating difference becomes. If both teams have identical ratings, the rating difference is zero and the 
predicted probability is exactly 0.5, meaning each team has an equal chance of winning. As the rating difference 
increases, the predicted probability gradually approaches 1 for the stronger team and 0 for the weaker team, without 
ever exceeding these limits.

The constant value of 400 controls the steepness of the logistic curve. A rating advantage of approximately 100 points 
corresponds to an expected win probability of around 64%, while a 200-point advantage corresponds to roughly 76%. 
Larger rating differences therefore produce increasingly confident predictions while still allowing upsets to occur.

This probability is then used to determine how much each team's rating should change after the game. Expected 
victories produce only small rating adjustments, whereas unexpected victories produce much larger changes, allowing 
the Elo ratings to adapt throughout the season.

This probability is calculated by the ```win_probability()``` method:
```python
def win_probability(self, team_a, team_b): 
    rating_a = self.ratings[team_a] 
    rating_b = self.ratings[team_b] 
    
    return 1 / (1 + 10 ** (-(rating_a - rating_b) / 400))
```

### Rating Updates
After each game, the predicted probability is compared with the actual result.

If the higher-rated team wins as expected, only a small rating adjustment is made.

If the lower-rated team wins unexpectedly, a much larger adjustment is applied.

The model updates the ratings using:

```rating += K × (Actual − Expected)```

where:
* Actual is either 1 (win) or 0 (loss).
* Expected is the predicted win probability.
* K controls how quickly ratings change.

This allows the ratings to continually adapt throughout the season while remaining relatively stable over long periods.

### Choice of K-Factor
The K-factor determines the sensitivity of the Elo system.

For this project a value of:

```K = 20```

was selected.

A larger K-factor causes ratings to change rapidly after every game, making the system highly responsive but also more 
volatile. Conversely, a smaller K-factor results in more stable ratings that require many games before significant 
changes occur.

A value of 20 provides a balance between stability and responsiveness and is commonly used as a starting point in 
many Elo implementations. Future iterations of this project may investigate alternative K-values through backtesting 
to determine which produces the most accurate predictions.

### Initial Team Ratings
At the beginning of each season, every NBA team is assigned an initial Elo rating of:

1500

This represents a neutral starting point where all teams are assumed to have equal strength 
before any games have been played.

As the season progresses, ratings gradually diverge according to each team's performance.

### Implementation of the EloModel Class
The Elo rating system was implemented as a dedicated EloModel class to separate the rating logic 
from the data-loading process.

The class contains several methods, each responsible for a specific task:
* ```__init__()``` initialises the model parameters, including the K-factor, the initial rating, a dictionary of 
current team ratings, and a history list for storing Elo progression.
* ```initialize_teams()``` identifies every team appearing in the dataset and assigns each an initial rating of 1500.
* ```win_probability()``` calculates the expected probability that one team will defeat another using the Elo 
probability equation.
* ```update_ratings()``` updates both teams' ratings after every game according to the predicted and actual outcomes.
* ```fit()``` iterates through every game in chronological order, determines the winner, updates both teams' ratings, 
and records the new ratings in the history log.
* ```get_ratings()``` returns the current Elo ratings for all teams.
* ```get_rankings()``` sorts the teams from highest to lowest Elo rating.
* ```get_history()``` converts the stored rating history into a pandas DataFrame, allowing the ratings to be 
analysed or visualised later.
