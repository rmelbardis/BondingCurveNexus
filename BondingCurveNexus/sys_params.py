'''
Define opening & fixed system parameters for simulation
'''
import requests

# DUNE VALUES TODAY - UPDATES REQUIRED REGULARLY #
# TODO: pull these in automatically
act_cover_now = 30_104
cap_pool_now = 101_773

# coingecko price api
price_url = 'https://api.coingecko.com/api/v3/simple/price'
# eth price from coingecko api
eth_price_params = {
        'ids':'ethereum',
        'vs_currencies': 'usd'
        }
eth_price_usd = requests.get(price_url, params=eth_price_params).json()['ethereum']['usd']

pool_dai = 5_040_000
pool_eth = cap_pool_now - (pool_dai / eth_price_usd)

# wnxm price from coingecko api
wnxm_price_params = {
        'ids':'wrapped-nxm',
        'vs_currencies': 'eth'
        }
wnxm_price_now = 0.021 #requests.get(price_url, params=wnxm_price_params).json()['wrapped-nxm']['eth']

# wnxm supply from coingecko api
wnxm_supply_url = 'https://api.coingecko.com/api/v3/coins/wrapped-nxm'
wnxm_supply_now = requests.get(wnxm_supply_url).json()['market_data']['total_supply']

# nxm supply from coingecko api
# nxm_supply_url = 'https://api.coingecko.com/api/v3/coins/nxm'
nxm_supply_now = 4_733_947 # requests.get(nxm_supply_url).json()['market_data']['total_supply']

# SYSTEM PARAMETERS - CURRENTLY FIXED BUT MAY BE SUBJECT TO CHANGE #
capital_factor = 4.8
mcr_now = act_cover_now / capital_factor

# NEW TOKENOMIC PARAMETERS #

# opening and target liquidity in ETH
# below book/sell pool (also used for single liquidity)
open_liq_sell = 10000
target_liq_sell = 10000
# above book/buy pool
open_liq_buy = 10000
target_liq_buy = 10000

# ratchet mechanism speeds
ratchet_up_perc = 0.04
ratchet_down_perc = 0.04

# liquidity injection speed
liq_in_perc = 0.04
liq_out_perc = 0.04

# oracle buffer
oracle_buffer = 0.01

# Zone Parameters for low capitalisation range
# ETH amount on top of MCR + target_liq_b required for BV as ratchet target
price_transition_buffer = 2500
# ETH amount on top of MCR + target_liq_b + price_transition_buffer
# where liq_eth_a = liq_eth_b
transition_gap = 1000
# ETH amount on top of MCR + target_liq_b + price_transition_buffer + transition_gap
# Where we start moving from separate liquidity parameters to liq_eth_a = liq_eth_b after every trade
liq_transition_buffer = 2500
