# NBA Playoff Prediction Simulator Project Development Document

# Model 0

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

## Elo Result...
Here is the result from running the elo simulation for the 2025-26 NBA season:
```
San Antonio Spurs 1702.7645765619857
Oklahoma City Thunder 1693.6747482082196
Boston Celtics 1656.345444496241
Detroit Pistons 1652.6099324003906
Denver Nuggets 1638.6895665011407
Los Angeles Lakers 1609.632198194759
New York Knicks 1606.8051076985585
Cleveland Cavaliers 1603.5980557776145
Houston Rockets 1588.8950374336653
Charlotte Hornets 1587.7282815929339
Atlanta Hawks 1571.8963115964827
Minnesota Timberwolves 1557.7172397527734
Orlando Magic 1541.4554404251562
LA Clippers 1535.8021863401527
Philadelphia 76ers 1529.8455993351906
Toronto Raptors 1527.4355117006967
Portland Trail Blazers 1524.2142524023357
Phoenix Suns 1519.0317086414063
Miami Heat 1507.3732636074249
Golden State Warriors 1425.1232739956627
Milwaukee Bucks 1401.2519703906705
New Orleans Pelicans 1398.6174368268241
Chicago Bulls 1369.1993750860888
Dallas Mavericks 1365.6256767394816
Sacramento Kings 1358.4148470914922
Indiana Pacers 1326.0412021621241
Memphis Grizzlies 1311.2574256013738
Utah Jazz 1310.45582266104
Brooklyn Nets 1310.2542106454882
Washington Wizards 1268.244296132625
```

Thus, based on this basic elo model we can see that the San Antonio Spurs are the best team in the NBA. This result is 
not surprising as the Spurs made it to the NBA Finals that year


## Building the Playoff Simulator
With the Elo ratings fully trained on the regular season dataset, the final stage of the project was to build a 
playoff simulation engine. The purpose of this component is to take the final Elo ratings and repeatedly simulate 
playoff series to estimate championship probabilities.

At a high level, the simulator does three things:
1. Translates Elo ratings into single-game win probabilities
2. Simulates individual playoff games using randomness
3. Aggregates game outcomes into series and then full playoff brackets

This allows us to move from a deterministic ranking (Elo table) to a probabilistic forecast of playoff outcomes.

### Designing the Simulation Structure
Before writing any code, it was important to define the structure of an NBA playoff simulation.

The NBA playoffs are not a single-elimination tournament, they are a multi-round, best-of-seven series format. 
This introduces two key requirements:

* We must simulate series outcomes, not just games
* We must track bracket progression dynamically, since later matchups depend on earlier results

To handle this, the simulator was structured into three core components:

* ```simulate_game()``` → simulates a single game
* ```simulate_series()``` → simulates a best-of-seven matchup
* ```simulate_playoffs()``` → runs the full bracket

This separation ensures each layer of logic remains modular and testable.

### Core Function 1: Simulating a Single Game
At the lowest level, each game is simulated using the Elo-derived win probability:
```python
def simulate_game(self, team_a_id, team_b):
    prob = self.elo.win_probability(team_a_id, team_b)

    if random.random() < prob:
        return team_a_id
```
This function is the bridge between deterministic modeling and stochastic simulation.

* The Elo model gives a probability (e.g. 0.63)
* The simulator introduces randomness
* The result mimics real-world unpredictability

Without this step, the model would always output the higher-rated team winning,
meaning there would be no variance and no meaningful playoff distribution.

### Core Function 2: Simulating a Series (Best of 7)
The NBA playoffs are decided by series, not single games, so we extend the simulation:
```python
def simulate_series(self, team_a, team_b):

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
```
This function reflects real NBA dynamics where better teams are more likely to win over multiple games.
Thus, it reduces variance compared to single-game outcomes

Even a weaker team can win a game, but winning four times before the opponent is significantly harder, and this is
what Elo is designed to capture.

### Core Function 3: Simulating the Conference
While the earlier functions handle games and series in isolation, the NBA playoffs are structured around 
conference-based brackets. Each conference (Eastern and Western) produces one finalist, 
and only then do the winners meet in the NBA Finals.

To model this correctly, an additional layer was introduced: the ```simulate_conference()``` function.
```python
def simulate_conference(self, teams):

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
```

This function takes a list of 8 teams ordered by playoff seeding and simulates an entire conference bracket from the 
first round through to the conference champion.

#### First Round (Quarterfinals):
```python
first_round = [
    self.simulate_series(teams[0], teams[7]),  # 1 vs 8
    self.simulate_series(teams[3], teams[4]),  # 4 vs 5
    self.simulate_series(teams[1], teams[6]),  # 2 vs 7
    self.simulate_series(teams[2], teams[5])   # 3 vs 6
]
```

This explicitly encodes the NBA playoff seeding logic:

* Higher seeds are rewarded with theoretically easier matchups
* The bracket is fixed (not re-seeded each round)
* Upsets are still possible due to Elo-based randomness

Each ```simulate_series()``` call produces a dictionary containing:

* winner
* series outcome (optional metadata like games won/lost)

This structure is important because it preserves traceability of each round, not just the final result.

#### Conference Semifinals:
```python
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
```
Instead of recomputing or flattening results, the model explicitly uses:
```python
first_round[i]["winner"]
```
This ensures:

* Bracket dependencies are preserved
* No re-sorting or recalculating is required
* The simulation remains deterministic in structure but stochastic in outcome

#### Conference Finals:
```python
conference_finals = self.simulate_series(
    semifinals[0]["winner"],
    semifinals[1]["winner"]
)
```
At this stage, only two teams remain. The result determines the conference champion, who advances to the NBA Finals.

### Core Function 4: Simulating the Full Playoff Bracket
```python
def simulate_playoffs(self, east, west):
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
```

Once individual conference brackets were defined, the next step was to combine both conferences into a complete NBA playoff system.

This is handled by the ```simulate_playoffs()``` function.

#### Conference-Level Simulation:
```python
east_results = self.simulate_conference(east)
west_results = self.simulate_conference(west)
```
Each conference is simulated independently using the previously defined bracket logic.

This reflects the real NBA structure:

* Eastern Conference produces 1 champion
* Western Conference produces 1 champion
* These two teams advance to the Finals

This separation is important because it preserves conference independence until the Finals, exactly like the 
real league format.

#### NBA Finals Simulation:
```python
finals = self.simulate_series(
    east_results["winner"],
    west_results["winner"]
)
```
The Finals are treated as a standard best-of-seven series, consistent with earlier modeling assumptions.

#### Output Structure:
```python
return {
    "east": east_results,
    "west": west_results,
    "finals": finals,
    "champion": finals["winner"]
}
```

Instead of only returning the champion, the function returns the entire playoff pathway.

This enables:

* Path analysis (how each team reached elimination or victory)
* Upset tracking across rounds
* Debugging of bracket behavior
* Later visualization of full playoff trees

In other words, the model is not only predictive, it is also fully traceable.

### Core Function 5: Monte Carlo Playoff Simulation
While a single playoff simulation gives one possible outcome, the real goal is to estimate probabilities, 
not deterministic results.

To achieve this, a Monte Carlo simulation is introduced via ```simulate_many()```.

#### Running Repeated Simulations:
```python
champions = {}

for _ in range(n_simulations):
    results = self.simulate_playoffs(east, west)
    champion = results["champion"]
    champions[champion] = champions.get(champion, 0) + 1
```

Each iteration:

* Runs a full playoff simulation
* Extracts the champion
* Updates a frequency counter

Over many iterations, this builds a distribution of championship outcomes.

#### Converting Counts into Probabilities:
```python
for team in champions:
    champions[team] /= n_simulations
```
This normalises raw counts into probabilities:
$$
P(\text{champion}) = \frac{\text{number of wins}}{\text{total simulations}}
$$

The output is a dictionary of the form:
```python
{
    "Boston Celtics": 0.21,
    "Denver Nuggets": 0.18,
    "OKC Thunder": 0.15,
    ...
}
```

### The Critical Issue: Team Identity Mismatch Across Files:
At this stage, a major issue emerged. The team identifiers used in the Elo model did not consistently match the 
identifiers used in the playoff simulator input.

What caused the problem

The Elo model used:

* TEAM_NAME from ```LeagueGameLog```
* Full franchise names like "Los Angeles Lakers"

However, the playoff simulator input was built from:

* Abbreviations like "LAL"
* Or sometimes mixed formats like "LA Lakers"

This created a failure:

* Elo lookup worked for "Los Angeles Lakers"
* But playoff simulation queried "LAL"
* Result: missing keys, incorrect mappings, or crashes

This reveals a key assumption flaw:

I assumed all NBA datasets use a consistent team identifier format.

They do not.

#### The Fix:
The temptation at this point was to patch the symptom: build a translation dictionary that maps every 
possible name variant ("LAL" → "Los Angeles Lakers" → "LA Lakers") to a single canonical string, and 
sprinkle `.get()` lookups with fallbacks wherever a KeyError appeared. I actually went down this path 
first, in a separate debugging session — adding a `clean_name()` normaliser, a `TEAM_NAME_MAP` dictionary, 
`.get()` calls with `None` fallbacks, `dropna()` safety nets, and `assert` statements scattered across the 
loader. It "worked" in the sense that it stopped crashing immediately, but it just moved the failure further 
downstream — I ended up with dozens of `UNMAPPED GAME` warnings and an eventual `KeyError: nan` deep inside 
the simulator, because partial name-matching can never be made fully exhaustive. Every new endpoint or season 
risked introducing yet another naming variant.

The actual fix was to stop matching on names at all.

Both endpoints I was already using, `LeagueGameLog` and `LeagueStandings`, return a numeric `TEAM_ID` field 
directly. This ID is stable across endpoints, seasons, and naming conventions, because it identifies the 
franchise at the database level rather than via a display string. Once I noticed this, the name-matching 
problem disappeared entirely because there was nothing to match as both data sources already agreed on the 
same identifier.

```python
from nba_api.stats.static import teams

NBA_TEAMS = teams.get_teams()

TEAM_ID_TO_NAME = {
    t["id"]: t["full_name"]
    for t in NBA_TEAMS
}
```

`teams.py` keeps this single lookup table purely for display purposes, converting team IDs back into 
readable names when printing results. It is no longer used anywhere in the data pipeline itself.

`data_loader.py` was updated so that `HOME_TEAM` and `AWAY_TEAM` (and the neutral-site equivalents) store 
`TEAM_ID` instead of `TEAM_NAME`:

```python
grouped_games.append({
    "GAME_ID": game_id,
    "DATE": home["GAME_DATE"],

    "HOME_TEAM": home["TEAM_ID"],
    "AWAY_TEAM": away["TEAM_ID"],

    "HOME_PTS": home["PTS"],
    "AWAY_PTS": away["PTS"],

    "SITE_TYPE": "HOME_AWAY"
})
```

`elo.py` required no changes at all. Because the Elo model treats team identifiers as opaque dictionary 
keys, it never inspects or parses the string, swapping strings for integers was a drop-in change. This 
ended up being a good validation of the original design: keeping `EloModel` agnostic to what a "team" 
actually *is* meant the identity-mismatch bug could be fixed entirely at the data layer, without touching 
the model logic.

`playoff_simulator.py` similarly needed no structural changes, only the type flowing through it changed, 
from team name strings to team ID integers. The bracket logic, series logic, and Monte Carlo loop were 
already identifier-agnostic by design.

The only remaining piece was building the playoff bracket itself from `LeagueStandings`, which also exposes 
`TeamID` directly:

```python
standings = leaguestandings.LeagueStandings(season=SEASON).get_data_frames()[0]

east = (
    standings[standings["Conference"] == "East"]
    .sort_values("PlayoffRank")
    .head(8)["TeamID"]
    .tolist()
)
```

With this, `main.py` could run start to finish — train Elo on `TEAM_ID`-keyed games, pull seeding from 
standings as a list of `TEAM_ID`s, and feed both into the simulator, without a single name lookup, mapping 
dictionary, or `.get()` fallback anywhere in the pipeline.

#### Lesson learned: 
When two datasets disagree on how to represent the same real-world entity, the fix is 
almost never a better translation layer between them, it's finding the identifier they already agree on 
and using that instead. The name-matching approach felt productive because it produced visible progress 
(fewer crashes per iteration), but it was solving the wrong problem. The moment I checked whether `TeamID` 
existed in both API responses, the "fix" became a deletion of code rather than an addition of more of it.

# Model 0 (Baseline Elo) - results:
```
Championship Odds:
San Antonio Spurs         28.7%
Oklahoma City Thunder     25.5%
Boston Celtics            14.7%
Detroit Pistons           13.2%
Denver Nuggets            5.8%
Cleveland Cavaliers       3.6%
New York Knicks           3.2%
Los Angeles Lakers        2.4%
Houston Rockets           1.1%
Atlanta Hawks             0.9%
Minnesota Timberwolves    0.3%
Philadelphia 76ers        0.2%
Orlando Magic             0.2%
Toronto Raptors           0.1%
Portland Trail Blazers    0.1%
Phoenix Suns              0.0%
```
This is the project's first concrete output, and it represents Model 0 from the roadmap: baseline Elo, no 
adjustments for home court, recent form, matchups, or injuries. Every team's win probability in every 
simulated game comes from nothing more than its end-of-regular-season Elo rating.


## Comparing to actual NBA results:
Now that we have these probabilities, we can compare them to the real result of the NBA.

My first thought was to do a **backtest**. However, after implementing this I quickly realised there was
a fundamental conceptual problem with how I was thinking about it.

#### The Problem with Comparing Probabilities to a Single Outcome:

Because we are running Monte Carlo simulations, what we get back is a probability distribution, not a
prediction. We are not saying "this team will win", we are saying "this team wins X% of the time across
many simulated universes".

The problem is that real life only has one universe. The playoffs happen once. OKC either wins or they don't.

So if our model gives OKC a 30% championship probability and they win, does that mean the model was right?
Wrong? We have no way of knowing from a single season. A 30% event happening once tells us nothing, it was
supposed to happen 30% of the time anyway.

The same problem applies at the series level. If our model says Team A has a 65% chance of winning a series
and Team B wins, that doesn't mean the model was wrong. It means the 35% outcome happened.

This means the naive approach of "did the model pick the right champion?" is essentially useless as an
evaluation metric. It punishes the model for randomness, not for being bad.

### The Solution: Brier Score:
After thinking this through, the right tool for evaluating probabilistic forecasts is the **Brier Score**.

#### What is a Brier Score:
The Brier score was introduced by American meteorologist Glenn W. Brier.

He published the measure in 1950 in the Monthly 
Weather Review to measure the accuracy and reliability of probability-based weather forecasts

A Brier Score is a metric used to measure the accuracy and calibration of probabilistic predictions 
for binary or categorical events (e.g., forecasting a 30% chance of rain). 

It calculates the mean squared difference between the predicted probabilities and the actual outcomes

Therefore, in the case for our project:

instead of asking "did the right team win?", it asks "how wrong were the probabilities, on average?"

For each team, we have:
* `p` = the model's predicted championship probability
* `outcome` = 1 if they actually won, 0 if they didn't

The Brier Score is:

$$
\text{Brier Score} = \sum_{i=1}^{K} (p_i - o_i)^2
$$

* 0 (Perfect Accuracy): The forecast perfectly predicted the outcomes.
* 0.25 (Random Guessing): A 50/50 probability assigned to every event.
* 1 (Total Inaccuracy): The forecast predicted a 100% chance for an event that did not happen, 
or a 0% chance for an event that did.

In short, a *lower* Brier score indicates a more accurate and reliable forecast.

A model that gave 30% to the real champion gets penalised less than a model that gave 5%.
A model that gave 95% to the wrong team gets hammered.

Crucially, this metric is meaningful across multiple seasons. By running the model on 15 historical
seasons and averaging the Brier scores, we get a single number that tells us how good the model actually
is, and more importantly, we can compare this number across Model 0, Model 1, Model 2, etc. to see
whether each new feature genuinely improves the forecast.

For reference, a naive model that assigns every team an equal 1/16 chance scores 0.9375.
If our model can't beat that, something is seriously wrong.

Naive model:

$$
\text{Naive Brier Score} = \left(\frac{1}{16}-1\right)^2 + 15\left(\frac{1}{16}-0\right)^2 = 0.9375
$$


### Implementation:
I created a `brier_score.py` file to house the scoring logic, and a `get_champion()` function in
`data_loader.py` to retrieve the actual champion for any historical season.

#### Getting the actual Champion:
```python
def get_champion(season):
    games = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star='Playoffs',
        player_or_team_abbreviation='T'
    )

    df = games.get_data_frames()[0]
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

    last_game_id = df.sort_values("GAME_DATE")["GAME_ID"].iloc[-1]

    final_game = df[df["GAME_ID"] == last_game_id]
    winner_row = final_game[final_game["WL"] == "W"].iloc[0]

    return int(winner_row["TEAM_ID"])
```

The logic here is simple: load all playoff games, find the last game played (which is always Game 4, 5, 6
or 7 of the Finals), and return the `TEAM_ID` of whoever had a W in that game. That team is the champion.

I initially tried a more complex approach, reconstructing the entire bracket round by round using the
round number embedded in the `GAME_ID` string. This quickly became a debugging nightmare because pandas
was storing `GAME_ID` as an integer, silently dropping the leading zeros, which caused the string indexing
to slice the wrong characters and return no Finals series at all. The bracket approach also wasn't necessary
at this stage since we only need the champion for the Brier score. The simple approach above, last game,
check WL, works reliably and is much easier to reason about.

#### Computing the Brier Score:
```python
def championship_brier_score(predicted_probs, actual_champion):
    total = 0.0

    for team_id, p in predicted_probs.items():
        outcome = 1 if int(team_id) == int(actual_champion) else 0
        total  += (p - outcome) ** 2

    return total
```

#### What the Brier Score Actually Tells Us

The real value of this metric only becomes apparent when we run it across multiple seasons. A single
season's Brier score tells us very little, it depends too much on whether the favoured team happened
to win that year. But averaged across 15 seasons, it becomes a stable signal.

This gives us a principled way to answer the core research question of the project: ***which
features actually improve playoff forecasting accuracy?***

### Brier Score Over 30 Seasons:
```
===========================================================
MODEL 0 — BACKTEST SUMMARY
===========================================================
SEASON       CHAMPION                       PRED %   BRIER
-----------------------------------------------------------
1996-97      Chicago Bulls                  31.2%    0.6210
1997-98      Chicago Bulls                  28.7%    0.6233
1998-99      San Antonio Spurs              39.3%    0.4120
1999-00      Los Angeles Lakers             55.6%    0.2273
2000-01      Los Angeles Lakers             17.3%    0.7925
2001-02      Los Angeles Lakers             11.5%    0.9288
2002-03      San Antonio Spurs              38.7%    0.4572
2003-04      Detroit Pistons                10.5%    0.9807
2004-05      San Antonio Spurs               4.1%    1.0587
2005-06      Miami Heat                      3.0%    1.1429
2006-07      San Antonio Spurs               7.6%    1.1187
2007-08      Boston Celtics                 46.3%    0.3256
2008-09      Los Angeles Lakers             22.9%    0.8035
2009-10      Los Angeles Lakers              2.9%    1.0947
2010-11      Dallas Mavericks                6.7%    1.1018
2011-12      Miami Heat                      6.6%    1.0770
2012-13      Miami Heat                     55.4%    0.2531
2013-14      San Antonio Spurs              29.3%    0.5490
2014-15      Golden State Warriors          47.4%    0.3203
2015-16      Cleveland Cavaliers             3.5%    1.3121
2016-17      Golden State Warriors          51.8%    0.2698
2017-18      Golden State Warriors           3.1%    1.2065
2018-19      Toronto Raptors                13.3%    0.8691
2019-20      Los Angeles Lakers             14.5%    0.9024
2020-21      Milwaukee Bucks                 7.0%    0.9771
2021-22      Golden State Warriors           1.8%    1.1153
2022-23      Denver Nuggets                  7.3%    1.0013
2023-24      Boston Celtics                 43.5%    0.3585
2024-25      Oklahoma City Thunder          52.9%    0.2786
2025-26      New York Knicks                 3.0%    1.1398
-----------------------------------------------------------
Average                                              0.7773
```
```
  Seasons completed : 30
  Uniform baseline  : 0.9375
  Model 0 avg Brier : 0.7773
  vs baseline       : -0.1602
```

The average Brier score across 30 seasons is 0.7773, compared to the uniform baseline of 0.9375.
This means Model 0 beats the naive "give every team an equal shot" benchmark by 0.1602, which confirms
the model is doing something real. It is not just noise.

#### Where the model does well

The clearest pattern is that the model rewards years where a genuinely dominant team entered the playoffs.

The best scores all cluster around these seasons:

| Season  | Champion              | Pred % |  Brier |
| ------- | --------------------- | -----: | -----: |
| 1999–00 | Los Angeles Lakers    |  55.6% | 0.2273 |
| 2012–13 | Miami Heat            |  55.4% | 0.2531 |
| 2016–17 | Golden State Warriors |  51.8% | 0.2698 |
| 2024–25 | Oklahoma City Thunder |  52.9% | 0.2786 |
| 1998–99 | San Antonio Spurs     |  39.3% | 0.4120 |

#### Where the model struggles
The flip side is that the model gets hammered in upset years:

| Season  | Champion              | Pred % |  Brier |
| ------- | --------------------- | -----: | -----: |
| 2015–16 | Cleveland Cavaliers   |   3.5% | 1.3121 |
| 2017–18 | Golden State Warriors |   3.1% | 1.2065 |
| 2005–06 | Miami Heat            |   3.0% | 1.1429 |
| 2025–26 | New York Knicks       |   3.0% | 1.1398 |
| 2006–07 | San Antonio Spurs     |   7.6% | 1.1187 |

A score above 1.0 means the model would have been better off assigning zero probability to the real
champion, that's how badly it got the probability wrong in those seasons. And some of these are
genuinely hard to explain.

The 2015-16 Cavaliers at 3.5% is the most extreme case. Cleveland came back from 3-1 down against those
Warriors in the Finals, the biggest upset in NBA Finals history. A model that gave them 3.5%
was not unreasonable going in, the market thought similarly. The Brier score just punishes the outcome
regardless of whether the forecast was sensible.

The 2017-18 Warriors at 3.1% is the most suspicious result as they were the most dominant team in NBA history, coming
off and NBA championship the yera prior and the best regular season record in NBA history 2 years prior (with a record 
of 73-9). This can be explained by the fact that this model only takes into account regular season results and during 
this season the Warriors were known for 'not taking games seriously' as they were just that much better than the 
competition.

However, this just shows that the model is still to naive and needs further iterations, which will obviously come in 
subsequent models.

#### What this number actually means for the project

The average Brier score of 0.7773 is now the benchmark that every subsequent model must beat.

The questions the project is asking, does margin of victory help? does home court help? does recent
form help?, all have a clean answer now. If Model 1 produces an average Brier score
below 0.7773 across the same 30 seasons, it is a better model. If it doesn't, that feature doesn't
add value.

That is the entire point of building the backtest infrastructure before building the next model.