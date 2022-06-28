'''
Define fixed modelling parameters for simulation
'''

# number of days to run the model for
model_days = 366

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
exit_loc = 100
exit_scale = 1

# normal distribution of daily change in active COVER AMOUNT
cover_amount_mean = 0.005
cover_amount_stdev = 0.07

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

# parameters related to closing wnxm gap to book value
# time preference of users
wnxm_discount_to_book = 0.05
# assumed single trade for closing the gap
gap_eth_sale = 10
# assume it takes 60 ETH to move the market 2%
# rough approximation according to sum of all exchanges in coingecko
wnxm_market_depth = 3000


# probability of exit per day of being in the exit queue at 100% book value
p_exit_full = 0.1
# exponent applied to ratio for exiting below book value
# e.g. if ratio of book value is 50%,
# multiplier of full daily exit prob is 0.5^exponent
p_exit_exponent = 8
