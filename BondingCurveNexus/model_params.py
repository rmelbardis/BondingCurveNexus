'''
Define modelling parameters for simulation
'''

import numpy as np

# number of days to run the model for
model_days = 730

#### ---- MARKET PARAMETERS ---- ####
# mean number of users entering and exiting the system
# to be modelled by poisson distribution, or used as deterministic number
lambda_entries = 0
lambda_exits = 40

# lognormal distribution of size of ENTRIES AND EXITS in ETH
# parameterised to median value being ~1 ETH, upper quartile ~3 ETH. Some 1000+ ETH buys/sells
entry_shape = 1.7
entry_loc = 0
entry_scale = 1

exit_shape = 1.7
exit_loc = 0
exit_scale = 1

# Deterministic entry/exit size (rounded up from ~4.3 ETH lognormal mean above)
det_entry_size = 5
det_exit_size = 5

# Deterministic entry array & exit array - numbers per day
det_entry_array = np.full(shape=model_days, fill_value=lambda_entries, dtype=int)
det_exit_array = np.full(shape=model_days, fill_value=lambda_exits, dtype=int)

# number of times the model shifts wnxm price randomly per day
wnxm_shifts_per_day = 5
# wnxm price movements (normal distribution of % change per shift)
wnxm_drift = 0
wnxm_diffusion = (1+0.02)**(1/wnxm_shifts_per_day) - 1

# wnxm price movement per eth of buy/sell pressure
# size based on 500,000 USD moving the price by 2% when wNXM price is 0.01 ETH
# Based roughly on coingecko +/-2% market depth, which typically hovers around ~$300k,
# but assuming here that markets will be deeper at higher prices
# fixed value in order to not be affected by day-to-day market movements
wnxm_move_size = 5e-7

# number of times we model the ratchets and liquidity shifting per day
ratchets_per_day = 10
liq_moves_per_day = 10

#### ---- NON-MARKET SYSTEM PARAMETERS ---- ####
# normal distribution of daily % change in active COVER AMOUNT
cover_amount_mean = 0.001
cover_amount_stdev = 0.01

# lognormal distribution of daily PREMIUM INCOME
# parameterised to have median value of a handful of ETH,
# upper quartile around 10 ETH and the occasional multi-million $ day
premium_shape = 2
premium_loc = 0.02
premium_scale = 3

# annual investment income %
investment_apy = 0.02
daily_investment_return = (1 + investment_apy) ** (1 / 365) - 1

# CLAIM frequency
claim_prob = 0.03

# lognormal distribution of claim size
# parameterised to have values of at least 1 ETH, the median value to be ~9 ETH,
# upper quartile around 30 ETH and the occasional multi-million payout
claim_shape = 2
claim_loc = 1
claim_scale = 15

# claim assessment reward (assuming premium was 1% of claim size)
claim_ass_reward = 0.002
