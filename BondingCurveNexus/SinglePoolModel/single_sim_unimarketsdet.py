'''
Running a single deterministic simulation of the market parameters only:
 - buying from protocol
 - selling to protocol
 - wNXM-NXM arbitrage
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params, model_params
from BondingCurveNexus.uni_markets_det import UniMarketsDet
from BondingCurveNexus.model_params import model_days

#-----GRAPHS-----#
def show_graphs():
    # Destructuring initialization
    fig, axs = plt.subplots(4, 2, figsize=(15,20))
    fig.suptitle('''Deterministic Market Model - varying sell pressure between first 180 days and subsequently.
                 Open Liq = 25,000, Target Liq = 2500, Ratchet = 4% of Book Value/day
                 Liquidity movement/day resulting in 100 ETH max injection/removal.
                 Buy pressure = 100 entries at 5 ETH/day''', fontsize=16)
    fig.tight_layout(w_pad=2, h_pad=2)
    fig.subplots_adjust(top=0.88)

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
    axs[3, 1].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq_sell))
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

    sim = UniMarketsDet()
    days_run = 0

    for i in tqdm(range(model_days)):
        try:
            sim.one_day_passes()
            days_run += 1
        except ZeroDivisionError:
            print('Something went to Zero!')
            break
