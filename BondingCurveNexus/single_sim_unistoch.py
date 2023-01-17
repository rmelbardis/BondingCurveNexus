'''
Running a single stochastic simulation of the market parameters only:
 - buying from protocol
 - selling to protocol
 - wNXM market movements
 - wNXM-NXM arbitrage
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params
from BondingCurveNexus.uni_markets_stoch import UniMarketsStoch
from BondingCurveNexus.model_params import model_days


#-----GRAPH FUNCTION-----#
def show_graphs():
    # Destructuring initialization
    fig, axs = plt.subplots(4, 2, figsize=(15,20))
    # set & format title of whole graph system
    fig.suptitle('One-sided Stochastic Model - 1.2 ratio of buys/sales', fontsize=16)
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)

    # Subplot
    axs[0, 0].plot(range(days_run+1), sim.nxm_price_prediction)
    axs[0, 0].set_title('nxm_price')
    # Subplot
    axs[0, 1].plot(range(days_run+1), sim.wnxm_price_prediction)
    axs[0, 1].set_title('wnxm_price')
    # Subplot
    axs[1, 0].plot(range(days_run+1), sim.book_value_prediction)
    axs[1, 0].set_title('book_value')
    # Subplot
    axs[1, 1].plot(range(days_run+1), sim.cap_pool_prediction)
    axs[1, 1].set_title('cap_pool')
    # Subplot
    axs[2, 0].plot(range(days_run+1), sim.nxm_supply_prediction)
    axs[2, 0].set_title('nxm_supply')
    # Subplot
    axs[2, 1].plot(range(days_run+1), sim.wnxm_supply_prediction)
    axs[2, 1].set_title('wnxm_supply')
    # Subplot
    axs[3, 0].plot(range(days_run+1), sim.liquidity_nxm_prediction)
    axs[3, 0].set_title('liquidity_nxm')
    # Subplot
    axs[3, 1].plot(range(days_run+1), sim.liquidity_eth_prediction)
    axs[3, 1].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq))
    axs[3, 1].set_title('liquidity_eth')
    # # Subplot
    # axs[4, 0].plot(range(days_run+1), sim.nxm_burned_prediction)
    # axs[4, 0].set_title('nxm_burned')
    # # Subplot
    # axs[4, 1].plot(range(days_run+1), sim.nxm_minted_prediction)
    # axs[4, 1].set_title('nxm_minted')
    # # Subplot
    # axs[5, 0].plot(range(days_run+1), sim.eth_sold_prediction)
    # axs[5, 0].set_title('eth_sold')
    # # Subplot
    # axs[5, 1].plot(range(days_run+1), sim.eth_acquired_prediction)
    # axs[5, 1].set_title('eth_acquired')
    # # Subplot
    # axs[6, 0].plot(range(days_run+1), sim.wnxm_removed_prediction)
    # axs[6, 0].set_title('wnxm_removed')
    # # Subplot
    # axs[6, 1].plot(range(days_run+1), sim.wnxm_created_prediction)
    # axs[6, 1].set_title('wnxm_created')

    plt.show()


if __name__ == "__main__":

    sim = UniMarketsStoch()
    days_run = 0

    for i in tqdm(range(model_days)):
        try:
            sim.one_day_passes()
            days_run += 1
        except ZeroDivisionError:
            print('Something went to Zero!')
            break
