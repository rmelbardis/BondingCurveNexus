'''
Define opening & fixed system parameters for simulation
'''
import requests

# NEXUSTRACKER VALUES TODAY - UPDATES REQUIRED REGULARLY #
# TODO: pull these in automatically
act_cover_now = 125_280
cap_pool_now = 145_832

# coingecko price api
price_url = 'https://api.coingecko.com/api/v3/simple/price'
# eth price from coingecko api
eth_price_params = {
        'ids':'ethereum',
        'vs_currencies': 'usd'
        }
eth_price_usd = requests.get(price_url, params=eth_price_params).json()['ethereum']['usd']

# wnxm price from coingecko api
wnxm_price_params = {
        'ids':'wrapped-nxm',
        'vs_currencies': 'eth'
        }
wnxm_price_now = requests.get(price_url, params=wnxm_price_params).json()['wrapped-nxm']['eth']

# wnxm supply from coingecko api
wnxm_supply_url = 'https://api.coingecko.com/api/v3/coins/wrapped-nxm'
wnxm_supply_now = requests.get(wnxm_supply_url).json()['market_data']['total_supply']

# nxm supply from coingecko api
nxm_supply_url = 'https://api.coingecko.com/api/v3/coins/nxm'
nxm_supply_now = requests.get(nxm_supply_url).json()['market_data']['total_supply']

# SYSTEM PARAMETERS - CURRENTLY FIXED BUT MAY BE SUBJECT TO CHANGE #
capital_factor = 4.8

# NEW TOKENOMIC PARAMETERS #

# opening and target liquidity in ETH
open_liq = 25_000
target_liq = 2500

# ratchet mechanism speed
ratchet_up_perc = 0.04
ratchet_down_perc = 0.04

# liquidity injection speed
liq_in_perc = 0.04
liq_out_perc = 0.5
