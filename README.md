# IXSwap Economics stress-testing
- <a href="">Trading Activity</a> (to be added)
- <a href="https://github.com/IX-Swap/models-testing/tree/amm">AMM prototype and simulations</a>

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