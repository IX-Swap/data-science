
## Trading activity simulation

The comparison between different trade-size distributions and the step-by-step process of estimating the parameters is contained inside the folder `paraneter_estimation`:

- `paramer_estimation/trade_size_dist_parameters_estimation_selected_pools.ipynb` - intermediate results based on a sample of pools
- `paramer_estimation/trade_size_dist_parameters_estimation_all_pools.ipynb` - final results, based on 200+ pools

### Traders Simulation Summary
The examined use-case are pairs composed of a non-traded security (X) and stablecoin (Y). The primary assets taken into consideration are private equity and real estate assets.

The stream of trades will come from a random process that “draws” trades from distributions. As in case of non-traded securities there are no alternative markets that would stimulate arbitrage activity in case of significant price differences, it’s reasonable to assume that the behavior of traders for each side (those willing to exchange X on Y and vice-versa) can be described by separate distributions, varying the parameters of which it would be possible to model distinct trading behaviors. 
The main parameters needed to describe the behavior of traders for each side are:
- Trade frequency - drawn from a poisson distribution with parameter Lambda (λ - is the expected rate of occurrences every minute)
- Trade size -  the distribution allowing to describe the traders best is to be determined

## Best-fit trade size distribution
The parameters for the trade-size distribution were estimated for stablecoin swaps in transactions, based on the reserve ranges at the moment of their execution. The following stablecoin reserve ranges were considered:
- 0 - 1 000
- 1 000 - 10 000
- 10 000 - 50 000
- 50 000 - 100 000
- 100 000 - 200 000
- 200 000 - 500 000
- 500 000 - 1 000 000
- 1 000 000 - 10 000 000
- 10 000 000 - 1 000 000 000

For each range, the parameters have been estimated separately, as the liquidity directly affects size of swaps (traders are much less likely to execute bigger swaps inside pools with small liquidity, because of the high price impact).

Four distinct trade-size distributions were considered: LogNormal, Gamma, Weibull, HalfCauchy. Chosen metrics for fit comparison: SSE, MAE, AIC. Applied visual comparison methods: Histograms, QQ-Plots, probability plots. 

Bellow is shown the table highlighting the performance of each considered distribution compared to the discussed metrics. Weibull distribution showed the best performance for describing the size of the swap.

<img src="/documentation/traders_simulation_images/dist_scores_total.png"/>
<figcaption align = "center"><b>Fig.1 - Final scores of each considered distribution, by metrics: AIC, SSE, MAE</b></figcaption>
</br>
</br>
The estimated parameters for each reserve range are shown in the graphs bellow:

<img  src="/documentation/traders_simulation_images/weibull_shape_curve.png"/>
</br>
<img src="/documentation/traders_simulation_images/weibull_scale_curve.png"/>
To select several cases based on which to conduct the simulations, the trade-size distribution parameters have been generalized. The generalized parameters are highlighted in red:(bellowisshown thesecondmethod...)
Bellow are presented the histograms of generated swaps for each combination of the generalized parameters for the reserve range 50 000 - 100 000. By conductions simulations for each of these cases, it would be possible to model different trader behaviours (tendency of performing either more smaller or bigger size swaps).
</br></br>
<img src="/documentation/traders_simulation_images/generalized_params_methodII.png"/>
