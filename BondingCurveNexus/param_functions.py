'''
Parameters for simulation that are derived from functions
'''

from BondingCurveNexus import sys_params

# opening liquidity based on input percentage of 'free' capital
def open_liq(liq_alloc_perc):
    return liq_alloc_perc * sys_params.free_capital

# movement in wNXM price, expressed as an ETH value
# based on 1 ETH worth of wNXM bought or sold
# takes USD value required to move wNXM price 2% based on current wNXM as input
def wnxm_movement_per_eth(two_perc_liq_usd):

    # find amount of ETH that it would take to move current wNXM price 2%
    two_perc_liq_eth = two_perc_liq_usd/sys_params.eth_price_usd

    # calculate the size of a 2% movement in terms of wNXM price in ETH
    two_perc_nxm_movement = sys_params.wnxm_price_now * 0.02

    # output wNXM price movement in ETH per 1 ETH of wNXM bought/sold on open market
    return two_perc_nxm_movement / two_perc_liq_eth
