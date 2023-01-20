'''
Running a set number of single deterministic simulations of the market parameters only:
 - buying from protocol
 - selling to protocol
 - wNXM-NXM arbitrage

 The purpose of this type of simulation is to test a range of parameters.
 Deterministic outcomes than then be compared to assess impact of varying this parameter.

 CURRENT SET-UP - SELL PRESSURE vs 100 BUYS/DAY
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params
from BondingCurveNexus.uni_markets_det import UniMarketsDet
from BondingCurveNexus import model_params
from BondingCurveNexus.model_params import model_days

#-----GRAPHS-----#
def show_graphs():
    fig, axs = plt.subplots(4, 2, figsize=(15,18)) # axs is a (6,2) nd-array
    fig.suptitle('''Deterministic Market Model Sell-only - varying initial liquidity.
                 Target Liq = 2500 Ratchet = 4% of Book Value/day
                 Liquidity movement/day resulting in 100 ETH max injection/removal.
                 Sell pressure = 20 exits at 5 ETH/day''', fontsize=16)
    fig.tight_layout(w_pad=2, h_pad=2)
    fig.subplots_adjust(top=0.88)
    # Subplot
    for i in range(len(sims)):
        axs[0, 0].plot(range(days_run+1), sims[i].nxm_price_prediction, label=label_names[i])
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].set_ylim(top=0.05, bottom=0)
    axs[0, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[0, 1].plot(range(days_run+1), sims[i].wnxm_price_prediction, label=label_names[i])
    axs[0, 1].set_title('wnxm_price')
    axs[0, 1].legend()
    # Subplot
    for i in range(len(sims)):
        axs[1, 0].plot(range(days_run+1), sims[i].nxm_supply_prediction, label=label_names[i])
    axs[1, 0].set_title('nxm_supply')
    axs[1, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[1, 1].plot(range(days_run+1), sims[i].wnxm_supply_prediction, label=label_names[i])
    axs[1, 1].set_title('wnxm_supply')
    axs[1, 1].legend()
    # Subplot
    for i in range(len(sims)):
        axs[2, 0].plot(range(days_run+1), sims[i].book_value_prediction, label=label_names[i])
    axs[2, 0].set_title('book_value')
    axs[2, 0].set_ylim(top=0.04, bottom=0)
    axs[2, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[2, 1].plot(range(days_run+1), sims[i].cap_pool_prediction, label=label_names[i])
    axs[2, 1].set_title('cap_pool')
    axs[2, 1].legend()
    # Subplot
    for i in range(len(sims)):
        axs[3, 0].plot(range(days_run+1), sims[i].liquidity_nxm_prediction, label=label_names[i])
    axs[3, 0].set_title('liquidity_nxm')
    axs[3, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[3, 1].plot(range(days_run+1), sims[i].liquidity_eth_prediction, label=label_names[i])
    axs[3, 1].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq))
    axs[3, 1].set_title('liquidity_eth')
    axs[3, 1].legend()
    # Subplot
    # for i in range(len(sims)):
    #     axs[4, 0].plot(range(days_run+1), sims[i].nxm_burned_prediction, label=label_names[i])
    # axs[4, 0].set_title('nxm_burned')
    # axs[4, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[4, 1].plot(range(days_run+1), sims[i].nxm_minted_prediction, label=label_names[i])
    # axs[4, 1].set_title('nxm_minted')
    # axs[4, 1].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[5, 0].plot(range(days_run+1), sims[i].eth_sold_prediction, label=label_names[i])
    # axs[5, 0].set_title('eth_sold')
    # axs[5, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[5, 1].plot(range(days_run+1), sims[i].eth_acquired_prediction, label=label_names[i])
    # axs[5, 1].set_title('eth_acquired')
    # axs[5, 1].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[6, 0].plot(range(days_run+1), sims[i].wnxm_removed_prediction, label=label_names[i])
    # axs[6, 0].set_title('wnxm_removed')
    # axs[6, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[6, 1].plot(range(days_run+1), sims[i].wnxm_created_prediction, label=label_names[i])
    # axs[6, 1].set_title('wnxm_created')
    # axs[6, 1].legend()

    plt.show()


if __name__ == "__main__":

  # range of variables to test
    init_liq_range = [2500, 5000, 10_000, 25_000, 50_000]

    # create sims and label names for graphs
    sims = []
    label_names = []
    days = []

    for liq in init_liq_range:
        sys_params.open_liq = liq
        sims.append(UniMarketsDet(daily_printout_day=175))
        label_names.append(f'Initial ETH Liquidity = {liq}')

    for sim in sims:

        days_run = 0

        for i in tqdm(range(model_days)):
            try:
                sim.one_day_passes()
                days_run += 1
            except ZeroDivisionError:
                print('Something went to Zero!')
                break
        days.append(days_run)
