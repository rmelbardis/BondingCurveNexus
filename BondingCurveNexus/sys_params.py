'''
Define opening & fixed system parameters for simulation
'''
import requests

# NEXUSTRACKER VALUES TODAY - UPDATES REQUIRED REGULARLY #
# TODO: pull these in automatically
nxm_supply_now = 6_787_984
act_cover_now = 198_782
cap_pool_now = 153_476

# wnxm price from coingecko api
url = 'https://api.coingecko.com/api/v3/simple/price'
params = {
        'ids':'wrapped-nxm',
        'vs_currencies': 'eth'
        }
wnxm_price_now = requests.get(url, params=params).json()['wrapped-nxm']['eth']

# SYSTEM PARAMETERS - CURRENTLY FIXED BUT MAY BE SUBJECT TO CHANGE #
capital_factor = 4.8

# NEW TOKENOMIC PARAMETERS #

# Factor of free NXM that needs to be breached by cover amount
# before purchases are stopped
# composed of 20x potential staking leverage and syndicates operating a 50% QS (2x)
stake_ceil_factor = 40

# when MCR% < 1, duration in days for bond with extra interest
entry_bond_length = 30
# exponential curve shape
entry_bond_max_interest = 0.02
entry_bond_shape = 10

# minimum duration in days before users can get funds out
minimum_exit_period = 14

# number of days after reaching 100% book value that option can be used
option_exit_period = 30
# cost of option if not exercised
option_cost = 0.1

# when MCR% <=1, durations in days
# to 100% book value for withdrawing ETH for NXM
#
# base value - minimum duration to 100% book value
base_exit_days = 60
# maximum days linked to MCR%
mcrp_max_days = 153
mcrp_trigger = 1
mcrp_threshold = 0.8
# maximum days linked to relative size of exit queue
queue_max_days = 153
queue_trigger = 0.1
queue_threshold = 0.2
