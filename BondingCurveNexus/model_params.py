'''
Define fixed modelling parameters for simulation
'''

# number of days to run the model for
model_days = 730

# mean number of users entering and exiting the system
# to be modelled by poisson distribution
lambda_entries = 10
lambda_exits = 10

# lognormal distribution of size of ENTRIES AND EXITS in ETH
# parameterised to median value being ~1 ETH, upper quartile ~4-5 ETH
entry_shape = 2
entry_loc = 0
entry_scale = 1

exit_shape = 2
exit_loc = 0
exit_scale = 1

# normal distribution of daily change in active COVER AMOUNT
cover_amount_mean = 0.0065
cover_amount_stdev = 0.07
# on days where no cover is allowed, drop amount
cover_amount_drop = 4000

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

# wnxm price movements (normal distribution of % change per day)
wnxm_drift = 0
wnxm_diffusion = 0.0655

# entry and exit percentage change in price
wnxm_entry_change = 0.001
wnxm_exit_change = 0.001

# parameters related to closing wnxm gap to book value
# time preference of users
wnxm_discount_to_book = 0.1
# assumed single trade for closing the gap
gap_eth_sale = 200
# assume this increases nxm price by 5%
wnxm_arb_change = 0.05


# probability of actual exit
# set to same for short and long periods
p_exit = 0.95
# for exits below 100% mcr%
# if exit is successful, probability that exit is at 100% BV
p_exit_full_bv = 0.9
# if not at full book value:
# threshold of bv
exit_bv_threshold = 0.5
# probability that exit is somewhere above threshold
p_exit_above_threshold = 0.9
# currently 1% chance of exiting below 50% bv
