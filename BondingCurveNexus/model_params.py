#--------------------------------------------------#
# Define fixed modelling parameters for simulation #
#--------------------------------------------------#


dictionary = {
    # number of days to run the model for
    'model_days': 366,

    # mean number of users entering and exiting the system
    # to be modelled by poisson distribution
    'lambda_entries': 10,
    'lambda_exits': 10,

    # lognormal distribution of size of ENTRIES AND EXITS in ETH
    # parameterised to median value being ~1 ETH, upper quartile ~4-5 ETH
    'sale_shape': 2,
    'sale_loc': 0,
    'sale_scale': 1,

    # normal distribution of daily change in active COVER AMOUNT
    'cover_amount_mean': 0.005,
    'cover_amount_stdev': 0.07,

    # lognormal distribution of daily PREMIUM INCOME
    # parameterised to have median value of a handful of ETH,
    # upper quartile around 10 ETH and the occasional multi-million $ day
    'premium_shape': 2
    'premium_loc': 0.02
    'premium_scale': 3

    # annual investment income %
    'investment_apy': 0.02


    # probability of exit per day of being in the exit queue at 100% book value
    'p_exit_full': 0.1
}
