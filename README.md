# IXSwap Economics stress-testing
- <a href="">Perpetual analysis</a> (to be added)
- <a href="https://github.com/IX-Swap/models-testing/tree/amm">AMM prototype and simulations</a>

# Introduction

Current branch contains analysis of the Perpetual V1 and V2 mechanisms to see how they deal with trading activity on the futures crypto markets. Both versions have their own chapters with separate reviews because of the fundamental differences between realizations of those platforms. Current file will contain general description of the analysis, while more detailed view can be accessed in the files mentioned inside this readme and in separate document.

Considering that mostly versions of the V1 and V2 are similar, description of the V1 will cover the general concept of the Perpetual protocol and how it works, while description of the V2 will cover only differences with the V1. For each of the chapters will be specified notebooks that cover respective information. The overall structure:

* Perpetual V1:
  *  General description; 
  *  Positions and their changes;
  *  Leverage, margin and liquidations;
  *  Funding payments and its regulation;
  *  Problems with V1
* Perpetual V2:
  *  General description; 
  *  Positions and their changes;
  *  Providing liquidity and regulation;
  *  Funding payments and its regulation;
  *  Leverage or buying power. 

# Perpetual V1

## General description

Conform the documentation from the official website of the Perpetual protocol it represents an open source software project of a perpetual futures DEX which runs on the blockchain (in case of V1 it runs on the xDAI). Futures are derivatives (meaning that they are not representing the real assets), "virtual" assets that are following the price of the respective real asset. Traditional futures have an expiry date and the price of the asset is shifted back to the actual one at the expiry date. Perpetual futures do not have any expiry date and therefore price shift to the real one is made via using funding payments, when trader receives reward from the platform in case if current activity shifts local price to the real market one. Otherwise, trader is paying this reward to the platform for causing price shift too far from the real one.

In case of performing activity as a trader there are two options:

* Setting a long position. In this case trader expects price to go up and there is performed "purchase" of the respective virtual token. When trader closes long position there is performed a sell of those virtual tokens in the background and trader gets profit in case of a higher selling price compared to the original buying price;
* Setting a short position. In this case trader expects price decrease and performs "sell" of the virtual token. When trader performs close of the short position, platform buys those virtual tokens from the trader and trader gets profit if selling price was higher than the buying one.

Concept of the futures is based on the vAMM principle, which represents modified concept of the AMM. vAMM provides the same concept of liquidity providers (providing tokens for performing trades and receiving reward in a fees form) and traders (swapping available tokens), but instead of using real tokens as in case of AMM, vAMM uses synthetic tokens. Synthetic tokens provide option of making leveraged trades (in case of Perpetual, up to x10) based on collateral tokens locked in the platform "vault".

First generation of the vAMM (and the first version of the Perpetual) uses the same formula as in the standard AMM for price discovery (standard k-based formula), but adds concept of "leverage" used for making higher reserves and trades. Both the first and the second versions are using USDC as a collateral token.

All of the presented data was collected from the original Perpetual subgraph (link: https://thegraph.com/hosted-service/subgraph/perpetual-protocol/perp-position-subgraph?query=List%20PositionChanged%20events). There are two folders in the ```perpetual``` folder:

* ```data_collection``` - covers the first steps in performing data analysis with first tries in collecting the data and some initial data analysis notebooks.
* ```second_investigation_wave``` - covers advanced approach in performing the data analysis with search for the more "in-depth" info.

## Positions and their changes

As mentioned above there are two options for a trader to open a position: long and short. Each new position and its change causes shift the token price. 

In case of long position, price of the token is increasing on the platform. From overall perspective it covers concept of "optimistic expectations from token" and therefore price is increasing. In case of looking into the working mechanism can be seen that there actually was performed "purchase" of respective virtual token, decreasing its balance inside pool and leading to price increase for this token.

In case of a short position, price of the token is decreasing. From overall perspective it covers concept of "negative expectations from token" and therefore price will be decreasing. In the background, because of happening "token sell" process balance of those tokens inside pool will increase and their price will drop. Each position change (or each trade) causes trader to pay for the fees, 50% of which are going to the transaction fees pool and another 50% are directed into insurance fund (used for covering unexpected losses).

From actual point of view each change of the position represents swaps of virtual assets inside virtual pool, but conform concept, for example, decrease of the long position by 50% will be covered/made by opening a short position by the 50% size of the long position. Considering those properties it is possible to make "close" of the position via position on the other trading side with the same size. What happens actually in this time is that in case of having a 5 vETH long position trader is making a 5 vETH short position and in the background 5 vETH tokens are "sold" to the platform, closing the position and setting position balance of the trader to 0.

For tracking size of the position there is a "balance" of virtual assets locked for this trader. Negative value of the balance demonstrates short position, while positive value of the balance covers long position. Each new position (or position change) influences on the balance of this position.

Any price changes on the platform influence profits and losses extracted from the presented position. Considering that there is a possibility for a trader to make a position that will lead to the extreme losses it is required to have a regulation mechanism that will liquidate position in case of losses going too far and dangerously close to extracting all money that trader provided to the platform. This concept is regulated via concept of the position liquidation, which depends on the leverage and margin.

In the ```data_collection``` folder there are two files ```check_position_connections``` and ```check_position_connections_2``` covering initial steps in performing positions analysis with search for data connections/patterns. Considering that trader is able to close position via reducing position size independent from its side to 0, it was required to check if there are some patterns in opens/closes of the data. For that there are files ```positions_opens_closes_indexation``` covering the estimation of opened and closed positions ID for each of the traders on each of the pools. Analysis of this aspect is covered in ```analysis_opens_closes```.

During basic analysis of the data was discovered that there are many bots performing their activity on the platform. Therefore, their activity was analyzed in three files called as ```bots_analysis``` files based on the data from ```time_window_analysis```. 

To find aspects influencing collected profits and losses there is a need to dive into the file called as ```search_for_pnl_dependencies```. As one of the first steps in the "second investigation wave" there was verification of the daily PnL respective to different trading aspects (look for ```Daily_PnL_respective_to_different_aspects``` file inside package called ```second_investigation_wave```).

Considering presence of the bots on the platform with an option of having arbitrage (because of the difference between local price with the global one or on other markets) and to see if there is a great impact because of those arbitrages it was decided to compare behavior of the traders with local price distribution and FTX price distribution of the respective tokens. It is reviewed in the files ```positions_price_analysis```.

## Leverage, margin and liquidations

To understand regulation mechanism of the platform there is a need to dive into understanding of margin and leverage first, then going to the liquidation mechanism.

When trader is entering into the market he/she must provide some money as guarantee to the platform that it is going to take in case of trader getting losses. Those funds are specified as "margin" - money balance that can be used to pay for the losses. In case of getting profits this balance is becoming bigger, but in the case of losses it decreases.

Based on this "balance" or "margin" positions are opened and conform Perpetual specifications leverage can be set up to 10x. What does it mean? Leverage is a multiplier that can be applied to your position for increasing its capitalization and therefore take more tokens for setting long/short position. It means that in case of trader providing 100 USD of margin using leverage it will be possible to create a position with capitalization up to 1000 USD. With higher leverage value there are collected higher profits and higher losses (higher risk is paid with higher outcome).

First version of the Perpetual uses concept of "separate margin" meaning that for each pool (token) there must be specified a separate margin and trader has option of making trades on all of the pool (or with all tokens) in case of providing margin for all of them. The maintanance margin is equal to 6.25% meaning that in case of position margin ratio dropping below 6.25% position will be automatically liquidated to avoid losses that can not be covered by trader.

Trader is able to avoid liquidation via changing position to adapt to changing market conditions, make it smaller. It is important to understand that liquidation refers to complete close of the position by the third person, while changing position to 0 means "close" of the position by the trader himself/herself.

This aspect is analyzed in the file called as ```pnl_respective_to_margin_price``` in the ```perpetual``` folder, where is reviewed impact of the margin, leverage and price distributions on the collected profits or losses. The liquidation aspect is reviewed in the position analysis and the ```liquidation_experiments``` file.

## Funding payments

Previously, in the general description of the platform was mentioned that trader moving mark price farther from the index one are paying funding payments, while traders moving mark price closer to the index one are receiving those payments. Positive value of the payment in the tables means that trader paid funding payment (negative value means that trader received the payment). The overall mechanism can be described by the simple mechanism:

1. Mark price = 1000 USD | Index price = 1015 USD
   
   Short position pays funding
   
   Long position earns funding

2. Mark price = 1015 USD | Index price = 1000 USD
   
   Short position earns funding
   
   Long position pays funding

Funding payments are paid or received for all opened positions meaning that with paying funding payment margin is slowly decreasing and this can even lead to position liquidation. The mechanism behind settling the funding payment is in comparing contract price (price when position was estimated) to the spot price.

Detailed principles and formulas behind funding payment mechanisms can be found on the official Perpetual documentation.

## Problems with V1

Conform collected information was seen that traders mostly collect funding payments and there are small payments to the platform creating disbalance with more money going out of the platform. This leads to Perpetual platform losses that can lead to the critical situations on the platform. To understand problem behind this concept it is required to see one example.

Imagine that there is a PERP token with that launched with price equal to 5 USD. Current price is equal to 17 USD meaning that there is a need to open long positions and remain open until desired price would be achieved. No shorts are needed on this stage. If funding goes positive (meaning that traders start to pay funding payments), longs exit making funding payments values negative again (meaning that traders receive rewards again). It means that all traders and all positions can receive payments.

Conform official documentation another problem of the platform was in slow execution of the transactions (up to 5 seconds for transaction confirmation). There were also problems with node reliability leading to the cases of transaction confirmation time going up to several minutes.

There is one interesting aspect influencing both V1 and V2, which is not a problem, but creates some risks for the platform. Bots. They represent most of the activity presented on both platforms (most of the losses, profits, fees, payments) and in case of them leaving the platform there will appear an activity gap and it is questionable if count of real persons will be enough for Perpetual to work. Another problem is that in bots are able to collect extreme profits and have some giant positions on the platform. In case of those bots to leave there can appear a great gap, leading to instability of the platform and possible need to activate insurance funds (this happened during 16 May 2022, when entire Perpetual was shut down with further "sunset" because of the liquidation of the big position on the vCREAM market, link: https://messari.io/governor/proposal/d39e87eb-92ab-4ce9-a583-6818a47ed61e). This can be a unique case, but amount of bots present on the system, cases of the big positions maintained by those bots lead to the possibility of the new case, that can happend in the future.

# Perpetual V2

## General description

Overall concept of the Perpetual is similar to the V1, but with several improvements:

1. Faster transaction execution/confirmation because of using Optimism network;
2. Use of Uniswap V3 under the hood;
3. Liquidity provisions with leverage;
4. Cross-margin mechanism;
5. Concentrated liquidity;
6. Multi-collateral

Usage of the Uniswap V3 under the hood leads to interesting aspect of performing position changes. As was mentioned previously each position change in the background represents purchase/sell of the virtual token (swap) and each position change is represented by the swap of the token inside virtual pool on the Uniswap V3. While swaps on the Uniswap on real pools contain capitalization parameter depending on the prices of assets used in swaps, swaps of virtual tokens have capitalization equal to 0 (covering the aspect of 0 value for virtual tokens outside of the Perpetual platform). Because of the swap-based behavior of the system and structure of the vAMM it is possible to perform MEV attacks (such an option is even mentioned in the official documentation), but after analysis there were no attacks detected (there important notes in the respective chapter).

On the updated version of the Perpetual can be used leverage liquidity mechanism, giving maker an option to scale up amount of provided tokens virtually. Maker also specifies price range in which provided liquidity will be used with both of the provided tokens - concentrated liquidity mechanism. Conform this concept, maker specifies upper tick and lower tick - values that are used in a specific formula to demonstrate a price range where provided liquidity will be used on both sides. Closer is the exchange price to the central tick (value between upper and lower tick) and smaller is the tick range - bigger is the amount of fees collected by the maker. In case of the exchange price to go out of the specified price range there will be used only one of the provided tokens and no fee reward going to the maker.

While the first version of Perpetual suggested specification of the margin for each pool separately where position is opened, the second version uses concept of cross-margin. Conform it, trader sets a common margin that is used by all positions on all pools covered by this trader. To make it possible to "track" trader's positions and see when it is required to liquidate positions there is specified a limit for up to 5 pools (tokens) in parallel where trader is allowed to have positions.

To make work with Perpetual even more comfortable in the second version is introduced mechanism of the multi-collateral. For setting margin, getting fees and so on in the first version and in the beginning of the second one there was specified only USDC token. With multi-collateral update there are new options of setting other collateral tokens.

General and simple explanation of the data available on the Perpetual V2 subgraph is shown in the file ```description_of_tables```.

## Positions and their changes

The problem of the current subgraph realization if that it covers position-related data, but does not provide direct information about used buying power for this position (or leverage info) or margin info for this exact position. Therefore, it was required to reconstruct money balance for each trader separately and consider it for all opened at the moment positions. In case of further analysis it will be required to either consider this aspect, or to search for the margin (or leverage) info in the subgraph (maybe will appear in future updates).

Positions were analyzed in the files ```trader_position_changes_analysis``` (all respective parts), ```position_changes_detailed```, ```making_master``` (creation of the "master" table with all position-related info). There are also ```position_histories_detailed``` files with analysis of the removed table from the subgraph.

## Providing liquidity and regulation

The second version of Perpetual implemented concentrated liquidity mechanism and therefore it was required to review all liquidity provisions and updates to see behavior of the makers. This was reviewed in the files ```liquidity_analysis``` (both parts), ```liquidity_second_step```, ```making_maker_master```.

## Funding payments and its regulation

One of the main differences between funding payments on V1 and V2 is that V1 performed estimation of the funding payments on hourly basis, while V2 based funding payments are working on their estimation on the block-based principle. Considering that makers are also shifting the token price (depending on their tick range specified for liquidity provision) they are also paying the funding payments. The funding rate on V2 totally depends on the size of difference between local price and market one.

Detailed description of the funding payments working mechanisms - https://blog.perp.fi/block-based-funding-payment-on-perp-v2-35527094635e

This aspect of the platform was reviewed in the files ```funding_analysis```, ```funding_detailed``` and in files covering either position changes, or liquidity changes.

## Leverage or buying power

The problematic difference between V2 subgraph and V1 is that in the V1 was specified information about the margin, because each of the markets contained isolated margin for trader, meaning that it was not shared between pools (different opened positions). With shared margin specification of the trader margin is gone and the only way to find it was via calculation of the money balance per trader on the entire platform.

Leverage concept was replaced by the "buying power". Considering that right now margin is shared between all positions opened by the trader, used buying power is specified based on the capitalization of opened positions and "ratio" of used buying power per pool can be found as ratio of position capitalization to the money balance (or shared margin). In the documentation is specified approach for finding the money balance and tracking used buying power.

Those aspects are covered in the ```master_trader_analysis``` (all 3 parts)

## The main problem with Perpetual V2

Efficiency of the analysis performed over Perpetual V2 is questionable at the moment because of the applied updates to the platform and the subgraph of Perpetual through the entire time of performing data analysis and even at the moment of writing current readme. The second version of Perpetual has launched in November 2021 and therefore many pools (tokens) have small history with a small time window (some of the pools even appeared in the end of Winter 2022 and through Spring 2022).

Additional aspect that caused uniqueness of the taken time window is that during this time period started a crisis on many cryptomarkets and there were registered several drops in the token prices. Because of that, some of the demonstrated events are unique and do not cover expected behavior of the traders.

The first version of the Perpetual had downfall because of the extremely big position liquidation happened and during analysis of the Perpetual V2 was discovered that there is still a big part of the activity represented by the bots with big positions. Probability of the critical situation is smaller becuase of the fixed funding payment mechanism and increasing insurance funds, but it is required to consider such an option.