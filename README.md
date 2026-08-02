# How Predictable Are the NBA Playoffs?
#### Predicting NBA playoff outcomes using only information available before the playoffs begin.
Using Elo ratings, Monte Carlo simulation, injury modelling, and statistical analysis.

## Content & Documentation

### Project Development Journal:
Read about the development journey for this project. All the ups and downs, wins and losses - [Project Development Journal](project_development_journal.md)

### Content:
This project is being documented publicly throughout development.

#### 🎥 Full project breakdown video
* 🚧 Coming Soon 🚧

#### 📱 Development shorts/reels
* 🚧 Coming Soon 🚧

#### ✍️ Technical Substack articles
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
🚧 Planned 🚧

Additional feature:
* Late-season performance weighting

Question:
* Are teams entering the playoffs stronger or weaker than their season-long rating?

### Model 4 - Matchup Effects
🚧 Planned 🚧

Additional feature:
* Head-to-head regular-season performance

Question:
* Do specific matchups outperform generic team strength estimates?

### Model 5 - Bayesian Team Strength
🚧 Planned 🚧

Additional feature:
* Rating distributions rather than point estimates

Question:
* How should uncertainty in team strength affect playoff predictions?

### Model 6 - Injury Modelling
🚧 Planned 🚧

Additional feature:
* Injury probabilities 
* Player impact estimation
* Team impact when a star player is injured

Question:
* How much uncertainty do injuries introduce into championship forecasts?

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





