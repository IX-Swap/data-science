# IXSwap Economics stress-testing
- <a href="">Trading Activity</a> (to be added)
- <a href="https://github.com/IX-Swap/models-testing/tree/amm">AMM prototype and simulations</a>

# Introduction

Current repository contains two parts: traders activity simulation models with transaction histories and AMM market simulation. Current readme will cover general description of both parts in detail, referring to the inner project structure, code fragments and explaining some solutions closely. Each project part has its own branch and each branch will have a local readme file only about the part where it is inserted.

Current project contains Uniswap V2 pools transaction histories analysis shown in the PDF document ```IXS_pools_analysis_v2.pdf```. This readme explains implementation of the simulations and used/created algorithms conform next structure:

* [Traders activity simulations and structure](#traders-activity-simulations-and-structure):
  * [General description of the project structure](#general-description-of-the-project-structure)
  * [Monte Carlo simulations](#monte-carlo-simulations):
    * [Normal distribution generator](#normal-distribution-generator)
    * [Log-Normal distribution generator](#log-normal-distribution-generator)
    * [Pareto distribution generator](#pareto-distribution-generator)
    * [Cauchy distribution generator](#cauchy-distribution-generator)
    * [Gamma distribution generator](#gamma-distribution-generator)
    * [Weibull distribution generator](#weibull-distribution-generator)
    * [Monte Carlo transaction simulator](#monte-carlo-transaction-simulator)
    * [Simulations with best match to the real life distributions](#simulations-that-have-the-best-match-with-real-life-distributions)
    * [Parameter search algorithms](#parameter-search-algorithms)
  * [Transaction history](#transaction-history):
    * [Analysis strategy and performed data manupulations](#analysis-strategy-and-performed-data-manipulations)
    * [MEV attack](#mev-attack)
    * [How use of stablecoins in token pairs stabilizes distributions](#how-use-of-stablecoins-in-token-pairs-stabilizes-distributions)
* [MEV attacks analysis](#mev-attacks-analysis)
  * [Used code for performing analysis](#used-code-for-performing-analysis)
    * [Libraries](#libraries)
    * [Etherscan scrapper](#etherscan-scrapper)
    * [Pools simulations analysis and basic MEV attacks analysis Jupyter notebooks](#pools-simulations-analysis-and-basic-mev-attacks-analysis-jupyter-notebooks)
    * [MEV attacks analysis by their frequency, profits, gas spendings](#mev-attacks-analysis-by-their-frequency-profits-gas-spendings)
* [What's next?](#whats-next)

# Traders activity simulations and structure

## General description of the project structure

Current project is made out of the two parts: Monte-Carlo simulations and analysis of the collected trading activity from AMM pools of the Uniswap V2 and SushiSwap. Monte-Carlo simulations are separated by the first and second implementations. The first one was written during start of work over the project when only base data analysis was performed and only base mathematic models were used. Analysis of the trades was performed to solve several aspects:

* Understand trading behavior depending on token types, external factors influence on trades, time-depending market changes;
* Detect trading anomalies and performed attacks on the markets;
* Check how reserves, external markets prices and reputational changes define trading.

Branch ```ixs/transaction_simulations``` contains code with first implementation of the Monte-Carlo simulation, AMM simulation that is used to detect attacks performed on reviewed pools and check influence of the mitigation mechanism on trading with analysis of the collected trading data.

Branch ```amm``` contains enhanced realization of Monte-Carlo simulations with detailed analysis of different simulation approaches and comparison of their performance, experiments with different mitigation mechanism parameters, comparison of different market stress situations.

Considering subject complexity and amount of covered topics below is presented table of contents that will redirect you to a detailed explanation of all project parts and aspects.

* [Monte-Carlo simulation and used mathematical models](./documentation/monte_carlo_doc.md);
* [Transaction history analysis](./documentation/transaction_history_doc.md);
* Mitigation mechanism;
* [MEV attacks](./documentation/mev_attacks_analysis.md);

Obtained results, observations, important moments and conclusions are available in the document ```ixs_pools_analysis_v2.pdf```. Mentioned above chapters provide implementation description and only the most important conclusions.