## Simulations

The simulations are being conducted using <a href="historical_transactions">historical transactions</a> from distinct Uniswap v2 pools (the transaction history has been extracted through Uniswap subgraph), as well as using <a href="">custom transactions generator</a> (to be added).

### Historical Transactions
For each pair, simulations have been conducted with the default amm parameters without and with the volatility mitigation mechanism enabled. After that, 
a grid_run for distinct parameters has been performed, in order to visualize the pool behaviour and determine the optimal ones (not added yet, requires refactoring).

- <a href="historical_transactions/WBTC_DAI">WBTC/DAI</a> (low capitalization pool)
- WBTC/USDC (medium capitalization pool)
- ETH/USDC (high capitalization pool)
- ... and a lot more to be added after refactoring

## Prefix (E#)
The notebooks with simulations are prefixed with the letter E (experiment) followed by a number (identifier), which indicates the id of experiment (During one experiment several simulations can be conducted (e.g.: with/without volatility mitigation mechanism enabled, distinct dsw oracle params...) and generally this number represents the chronological order of the conducted simulation.
E.g.: E41_WBTC_DAI.ipynb


## AMM modifications (_mod#)
By the name of the simulation notebook, the amm set up used for conductiong the experiment can be determined.
The suffix at the end of the simulation notebook indicates the amm version used for processing the transactions or information about AMM-based parameters.
- **no suffix** (default amm set up, default params) (e.g.: WBTC_DAI.ipynb)
- **_mod1** - modification in dsw oracle: use the oldest price commulative observation which occured within 24 hours, if the one **24 hours** ago is not present
- **_mod2** - modification in dsw oracle: adding fallback_window_size = 48h - use the oldest price commulative observation which occured within **48 hours**, if the one 24 hours ago is not present
- **_W#** - simulation run with window size distinct from default (24h) (e.g.: WBTC_DAI_W48.ipynb - window size used = 48h)
- **_PT#** - simulation run with PRICE_TOLLERANCE_TRESHOLD distinct from default (=98) (e.g.: WBTC_DAI_PT_97.ipynb - price threshold used = 97)
- **_G#** - granularity

Note: the suffixes can be combined, to indicate the modification of more than one parameter (e.g.: WBTC_DAY_W12_PT97_G12.ipynb - simulation run with params: window size = 12, price tollerance threshold = 97, granularity = 12)

## Structure
Each pool has a dedicated folder containing
1. Simulation result analysis
2. Simulation result analysis, after modification in amm (see previous section)
3. Grid run analysis (not added yet, required refactoring for readability)
4. Individual analysis of *simulationss generated during grid run

*Not all of the simulations from the grid run are being analyzed individually, but only the ones which manifest an interesting or strange pattern during the overall grid run analysis
