# Nexus Mutual In-house Tokenomics Simulations

## Working with docker/ape/foundry

Build docker image and tag it as "ape":

`docker build . -t ape`

Mount current directory as `/app` inside the docker container, set current directory to `/app` and run the sim script using the ape image we've just created:

`docker run -it -v $PWD:/app -w /app ape`

This will run the simulation as specified in the `sim.py` file found in the 'scripts' directory.

If any changes are made to the sim.py file only, the simulation will automatically restart.

## Python-only simulation environment

Most up-to-date model: `BondingCurveNexus/HighLowCap`

The Python version of the model has recreated the intended operation of the RAMM in python only.

Key difference compared to the ape/foundry model is that the price ratchet and liquidity can update independently of any swap occuring. 

Each version contain a class that:
- initialises the system,
- captures the key variables and behaviours of the system,
- allows time to pass and
- tracks the change in variables over time.

The classes contain a `one_day_passes()` class method that simulates a single day's development of the system. It does this by creating a list of daily activities on the system based on the modelling parameters and shuffling them into a random order.
Running the simulations typically involves calling this method `model_days` times to create a longer simulation.

For both models, the parameters can be changed in the `sys_params` or `model_params` files in the `BondingCurveNexus` directory.

The `sys_params.py` file contains the variables that reflect the state of the system, such as:
- opening asset prices and supplies
- opening system state (e.g. capital pool size)
- RAMM parameters

The `model_params.py` file contains variables relating to model development behaviour, such as:
+ number of days the model is run for
+ buy/sell pressure - number and size of ETH-denominated entries/exits per day, either deterministic or as a distribution
+ wNXM market movement parameters, e.g., mean/st.dev of daily independent movements, price shift per ETH buy/sell
+ number of times ratchet/liquidity adjustment is applied per day

There are two kinds of models available - "Protocol", which captures only the features of the RAMM inside the Nexus Mutual system, and "Market", which adds some wNXM market features on top.

### Protocol Model

To run a single deterministic simulation of the model call `BondingCurveNexus/HighLowCap/single_sim_protocol_det.py`
The graphs can then be displayed in your environment using the `show_graphs()` function.

`one_day_passes` behaviours for Protocol model:

| Daily Behaviour  | Description |
| ------------- | ------------- |
| Ratchet & Liquidity  | Moves the prices of the Above and Below pools towards book value a specified number of times per day |
| Buys of NXM  | Users buying NXM from the Above Pool for ETH a number of times per day |
| Sells of NXM  | Users selling NXM to the Below Pool for ETH a number of times per day |

Variables tracked by the model in the `..._prediction` lists and displayed by `show_graphs()`

| Variable  | Description |
| ------------- | ------------- |
| cap_pool | Size of Capital Pool in ETH |
| spot_price_b | Spot price in Below pool |
| spot_price_a | Spot price in Above pool |
| nxm_supply | Total supply of NXM |
| book_value | Book Value (Capital Pool / NXM Supply) in ETH |
| liq | ETH liquidity in the RAMM |
| liq_NXM_b | NXM reserve in the Below pool |
| liq_NXM_a | NXM reserve in the Above pool |
| eth_sold | Cumulative ETH redeemed via the Below pool |
| eth_acquired | Cumulative ETH captured by the capital pool via the Above pool |
| nxm_burned | Cumulative NXM redeemed by users via the Below pool |
| nxm_minted | Cumulative NXM minted by users via the Above pool | 

### Market Model

To run a single deterministic simulation of the model call `BondingCurveNexus/HighLowCap/single_sim_markets_det.py`
The graphs can then be displayed in your environment using the `show_graphs()` function.

`one_day_passes` behaviours for Market model:

| Daily Behaviour  | Description |
| ------------- | ------------- |
| Arbitrage  | In between every daily event, the gap between the wNXM price and NXM price is closed via arbitrage, where possible. Either via (1) mint NXM in Above Pool -> wrap -> sell on open market OR (2) buy wNXM on open market -> unwrap -> redeem in Below pool |
| Ratchet & Liquidity  | Moves the prices of the Above and Below pools towards book value a specified number of times per day |
| Buys of NXM  | Users buying NXM from the Above Pool for ETH a number of times per day. If open market price is lower, buy wNXM instead |
| Sells of NXM  | Users selling NXM to the Below Pool for ETH a number of times per day. If open market price is higher, sell via wNXM instead |
| wNXM shift | Random market movements in wNXM price. Typically disabled for deterministic runs. |

Variables tracked by the model in the `..._prediction` lists and displayed by `show_graphs()` 

| Variable  | Description |
| ------------- | ------------- |
| cap_pool | Size of Capital Pool in ETH |
| spot_price_b | Spot price in Below pool |
| spot_price_a | Spot price in Above pool |
| wnxm_price | Open market price of wNXM |
| nxm_supply | Total supply of NXM |
| wnxm_supply | Total supply of NXM |
| book_value | Book Value (Capital Pool / NXM Supply) in ETH |
| liq | ETH liquidity in the RAMM |
| liq_NXM_b | NXM reserve in the Below pool |
| liq_NXM_a | NXM reserve in the Above pool |
| eth_sold | Cumulative ETH redeemed via the Below pool |
| eth_acquired | Cumulative ETH captured by the capital pool via the Above pool |
| nxm_burned | Cumulative NXM redeemed by users via the Below pool |
| nxm_minted | Cumulative NXM minted by users via the Above pool | 
| wnxm_removed | Cumulative wNXM unwrapped by arbitrageurs |
| wnxm_created | Cumulative NXM wrapped by arbitrageurs | 
