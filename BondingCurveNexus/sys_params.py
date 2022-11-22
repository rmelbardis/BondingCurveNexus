'''
Define opening & fixed system parameters for simulation
'''
import requests

# NEXUSTRACKER VALUES TODAY - UPDATES REQUIRED REGULARLY #
# TODO: pull these in automatically
nxm_supply_now = 6_779_309
act_cover_now = 149_632
cap_pool_now = 154_067

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
supply_url = 'https://api.coingecko.com/api/v3/coins/wrapped-nxm'
wnxm_supply_now = requests.get(supply_url).json()['market_data']['total_supply']

# SYSTEM PARAMETERS - CURRENTLY FIXED BUT MAY BE SUBJECT TO CHANGE #
capital_factor = 4.8

# NEW TOKENOMIC PARAMETERS #

# free capital
free_capital_perc = 0.5
free_capital = cap_pool_now * free_capital_perc

# ratchet mechanism speed
ratchet_up_perc = 0.005
ratchet_down_perc = 0.005
