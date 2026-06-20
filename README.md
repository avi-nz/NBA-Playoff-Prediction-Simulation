# NBA Playoff Prediction Simulation
Predicting NBA playoff outcomes using Elo ratings, Monte Carlo simulation, injury modelling, and statistical analysis.

## Content & Documentation

### Project Development Journal:
Read about the development journey for this project. All the ups and downs, wins and losses - [Project Development Journal](project_development_journal.md)

### Content:
This project is being documented publicly throughout development.

#### 🎥 Full project breakdown video

#### 📱 Development shorts/reels

#### ✍️ Technical Substack articles

## Overview
This project explores how accurately NBA playoff outcomes can be predicted using only information available before the playoffs begin.

The goal is to build a progressively more sophisticated forecasting system and evaluate the contribution of different predictive features, such as:

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
2. Which additions provide the largest improvement?
    * Home court advantage
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
10,000 / 50,000 / 100,000+ simulations

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
🚧 In Progress 🚧

Features:
* Standard Elo ratings
* No additional adjustments
  
Purpose:
* Establish benchmark performance

### Model 1 - Margin of Victory Elo
🚧 Planned 🚧

Additional feature:
* Incorporates point differential into Elo updates

Question:
* Does margin of victory improve playoff forecasting accuracy?

### Model 2 - Bayesian Team Strength
🚧 Planned 🚧

Additional feature:
* Rating distributions rather than point estimates

Question:
* How should uncertainty in team strength affect playoff predictions?

### Model 3 - Home Court Advantage
🚧 Planned 🚧

Additional feature:
* Home-court Elo bonus

Question:
* How much predictive value does playoff seeding provide?

### Model 4 - Recent Form
🚧 Planned 🚧

Additional feature:
* Late-season performance weighting

Question:
* Are teams entering the playoffs stronger or weaker than their season-long rating?

### Model 5 - Matchup Effects
🚧 Planned

Additional feature:
* Head-to-head regular-season performance

Question:
* Do specific matchups outperform generic team strength estimates?

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

Evaluation process:
* Compare forecasts against actual outcomes
  * This includes...
    * Comparing the forecasted champion to the real champion
    * Comparing results from each round
    * Comparing Games Won/Lost from each team





