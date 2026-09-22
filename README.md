# How Predictable Are the NBA Playoffs?
#### Predicting NBA playoff outcomes using only information available before the playoffs begin.
Using Elo ratings, Monte Carlo simulation, injury modelling, and statistical analysis.

---

> *"The biggest lesson that can be read from 70 years of AI research is that general methods
> that leverage computation are ultimately the most effective, and by a large margin."*
> — Rich Sutton, [The Bitter Lesson](http://www.incompleteideas.net/IncIdeas/BitterLesson.html) (2019)

This project is a small-scale demonstration of that lesson applied to sports prediction.
Six models were built, each encoding basketball domain knowledge that intuitively should
improve predictions — margin of victory, home court advantage, recent form, rating
uncertainty, and player injuries. Every single one either performed worse than the
baseline or produced no statistically significant improvement.

The baseline model knows nothing about basketball. It only knows who beat whom.
It was never beaten.

The lesson: the predictive signal is decent, but it is not in the places that ten years
of watching basketball suggested it would be. A general learning method, given the
right data and enough compute to discover its own features, would likely find what
actually moves the needle rather than what human intuition expects should.

---


## Content & Documentation

### Project Development Journal:
Read about the development journey for this project. All the ups and downs, wins and losses - [Project Development Journal](project_development_journal.md)

### Content:
This project is being documented publicly throughout development.

#### 🎥 Full project breakdown video
* 🚧 Coming Soon 🚧

#### 📱 Development shorts/reels
1. [Using Elo ratings to predict NBA champions](https://www.youtube.com/shorts/n90LS2hFiTY)

#### ✍️ Substack articles
1. [What Can Chess Teach Us About Predicting the NBA Playoffs?](https://avishainarsey.substack.com/p/what-can-chess-teach-us-about-predicting)
2. [Is All Winning Created Equal?](https://avishainarsey.substack.com/p/is-all-winning-created-equal)

## Overview
This project explores how accurately NBA playoff outcomes can be predicted using only information available 
*before the playoffs begin*.

The goal is to build a progressively more sophisticated forecasting system and evaluate the contribution of different 
predictive features, such as:

* Elo ratings
* Home court advantage
* Recent form
* Head-to-head matchups
* Injury uncertainty
* Star player dependence
* Bayesian uncertainty estimation

The final model will simulate thousands of playoff brackets to estimate championship probabilities for every team.

## Research Questions

This project investigates:

1. How accurately can a simple Elo model predict playoff outcomes?
2. Which additions provide improvement to the baseline Elo Model
    * Home court advantage
    * Margin of Victory
    * Recent form
    * Matchup effects
    * Injury modelling
    * Team dependence on star players
3. How sensitive are championship odds to injuries and uncertainty?
4. Can historical regular-season data be used to forecast future playoff success?

## Methodology

### Stage 1 - Elo Rating System
Estimate team strength using regular-season games.

Features:
* Dynamic Elo updates
* Expected win probabilities
* End-of-season team ratings

Output:
```
Team        Elo
-----       ----
Thunder     1710
Celtics     1690
Cavs        1640
Lakers      1570
```

### Stage 2 - Win Probability Model
Convert Elo differences into game win probabilities.

Example:
```
Celtics Elo: 1690
Lakers Elo: 1570

P(Celtics Win) = 67%
P(Lakers Win) = 33%
```

### Stage 3 - Monte Carlo Playoff Simulation
Simulate complete playoff brackets.

Process:
1. Calculate game win probability
2. Sample game outcome
3. Advance winner
4. Continue until champion

Repeat:
10,000 simulations

Example Output:
```
Team         Championship Odds
-----        ------------------
Celtics      31%
Thunder      27%
Nuggets      15%
Cavs         11%
Others       16%
```

## Model Roadmap

### Model 0 - Baseline Elo
✅ Complete

#### Substack Article:
* [What Can Chess Teach Us About Predicting The NBA Playoffs?](https://avishainarsey.substack.com/p/what-can-chess-teach-us-about-predicting)

#### Youtube short
* [Using Elo ratings to predict NBA champions](https://www.youtube.com/shorts/n90LS2hFiTY)

Features:
* Standard Elo ratings
* No additional adjustments
  
Purpose:
* Establish benchmark performance

Results (30 seasons, 1996-97 to 2025-26):
* Average Brier Score: **0.7773**
* Uniform baseline: 0.9375
* vs baseline: **-0.1602**

The model performs best in years with a dominant regular-season team (e.g. 1999-00 Lakers, 2012-13 Heat, 
2016-17 Warriors) and struggles in heavy upset years (e.g. 2015-16 Cavaliers, 2005-06 Heat). 
Beating the uniform baseline by 0.16 across 30 seasons confirms the Elo signal is real. 
This score is the benchmark every subsequent model must beat.

[Read the full results in the Project Development Journal](project_development_journal.md/#model-0-baseline-elo---results)

### Model 1 - Margin of Victory Elo
❌ Complete — No Improvement

#### Substack Article:
* [Is All Winning Created Equal?](https://avishainarsey.substack.com/p/is-all-winning-created-equal)

Additional feature:
* Incorporates point differential into Elo updates via a parameterised multiplier:
$ \frac{(point_{\mathrm{diff}} + a)^b}{c + d \cdot elo_{\mathrm{diff}}} $

Question:
* Does margin of victory improve playoff forecasting accuracy?

Answer: **No** — at least not by the metric that matters (which is champion prediction accuracy).

Results (30 seasons, 1996-97 to 2025-26):

* Model 0 avg Brier : **0.7773**
* Model 1 (log formula) : 0.8456 ❌
* Model 1 (538 formula) : 0.7853 ❌
* Model 1 (tuned params): 0.7867 ❌

Three different implementations were tested — a simple log formula, FiveThirtyEight's
empirical formula, and a version with parameters tuned to our own data via
`scipy.optimize`. All three produced worse championship Brier scores than Model 0.

The game-level Brier score did improve with the 538 and tuned formulas, suggesting
MoV adds signal for predicting individual regular season games. But this did not
translate to better playoff predictions. Regular season blowout margins appear to be
a poor proxy for playoff performance.

[Read the full results in the Project Development Journal](project_development_journal.md/#model-1---margin-of-victory)

### Model 2 - Home Court Advantage
❌ Complete — No Improvement

#### Substack Article:
* 

Additional feature:
* Home-court Elo bonus

Question:
* How much predictive value does playoff seeding provide?

Answer: **Almost none** 

Results:
- Fixed HCA:   0.7695 (not significant compared to Model 0, 15-15 season split)
- Dynamic HCA: 0.7750 (worse than fixed)

[Read the full results in the Project Development Journal](project_development_journal.md/#model-2---home-court-advantage)

### Model 3 - Recent Form
❌ Complete — No Improvement

Additional feature:
* Progressive K-factor that increases linearly from `k_start_mult` at game 1 to `k_end_mult` at game 82, weighting late-season performance more heavily

Question:
* Are teams entering the playoffs stronger or weaker than their season-long rating?

Answer: **No** — recent form weighting makes predictions worse, not better.

Results (30 seasons, 1996-97 to 2025-26):
* Model 0 avg Brier : **0.7773**
* Model 3 (k_start=0.5, k_end=1.5) : 0.8065 ❌
* Manual tuning toward 1.0/1.0 improved results incrementally, but only by converging back toward Model 0

The more aggressively late games are weighted, the worse the model performs. 
The likely explanation is **load management** — elite contenders routinely rest their stars in March and April, 
so their late-season record underrepresents their true strength. The progressive K-factor punishes them for this, 
inflating the ratings of fringe playoff teams grinding for seeding right up to game 82.

[Read the full results in the Project Development Journal](project_development_journal.md/#model-3---recent-form)


### Model 4 - Bayesian Team Strength
❌ Complete — No Improvement

Additional feature:
* Each team's final Elo rating is treated as the mean of a Normal distribution, with the spread derived from the 
standard deviation of their Elo ratings throughout the season — consistent teams get tight distributions, volatile 
teams get wide ones

Question:
* How should uncertainty in team strength affect playoff predictions?

Answer: **No improvement** — spreading probability away from heavy favourites hurts more than it helps.

Results (30 seasons, 1996-97 to 2025-26):
* Model 0 avg Brier : **0.7773**
* Model 5 avg Brier : 0.7832 ❌

The logic is sound but the data doesn't support it. The Elo standard deviation across a regular season captures 
schedule noise as much as genuine uncertainty about team strength. In dominant-team years — exactly when confident 
models score well — the Bayesian model is systematically less confident, and that costs it. 
The rest is not random enough to compensate.

[Read the full results in the Project Development Journal](project_development_journal.md/#model-5---bayesian-team-strength)

### Model 5 - Injury Modelling
⚠️ Out of Scope — Data Constraints

Additional feature:
* Per-game player availability probabilities based on official injury reports
* Player impact weighting by PIE share
* Elo penalty scaled by the importance of unavailable players

Question:
* How much uncertainty do injuries introduce into championship forecasts?

A prototype was implemented using regular season absence rates as a proxy for
per-game injury probability. This produced worse results than Model 0 (avg Brier
0.8271 vs 0.7773) due to two fundamental design flaws:

1. **Per-game rolling is wrong.** A player who missed 35% of the regular season
   had one injury that sidelined them for a block of games — not a 35% chance of
   missing any given playoff game independently. The prototype simulated them as
   randomly available throughout every playoff series, which is not how injuries work.

2. **Regular season absences include load management.** Elite players on contending
   teams deliberately sit out regular season games to rest for the playoffs. The model
   cannot distinguish genuine injury risk from strategic rest, and these have opposite
   implications for playoff performance.

The correct implementation requires official NBA injury report data — pre-series
availability statuses (Out / Doubtful / Questionable / Probable) for each player
going into each playoff round. These would be treated as fixed series-level statuses
rather than per-game rolls.

The NBA has only published structured official injury reports since approximately
2014-15, and historical reports exist only as PDFs. No public API provides clean
historical injury report data back to 1996. A proper backtest across 30 seasons
is therefore not feasible with publicly available data.

This feature is left as a direction for future work requiring either a paid data
provider or a purpose-built historical PDF scraper.

[Read the full results in the Project Development Journal](project_development_journal.md/#model-6---Injury-Modelling)

## Historical Backtesting
The model will be evaluated on previous NBA seasons.

Target seasons:
* 1996
* 1997
* 1998
* 1999
* 2000
* 2001
* 2002
* 2003
* 2004
* 2005
* 2006
* 2007
* 2008
* 2009
* 2010
* 2011
* 2012
* 2013
* 2014
* 2015
* 2016
* 2017
* 2018
* 2019
* 2020
* 2021
* 2022
* 2023
* 2024
* 2025
* 2026

*(These are all the seasons from the play-by-play era)*

Evaluation process:
* Compare forecasts against actual outcomes
  * This includes...
    * Comparing the forecasted champion to the real champion





