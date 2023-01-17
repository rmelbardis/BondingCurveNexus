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
from BondingCurveNexus.uni_protocol_det import UniProtocolDet
from BondingCurveNexus.uni_markets_det import UniMarketsDet
from BondingCurveNexus import model_params
from BondingCurveNexus.model_params import model_days

#-----GRAPHS-----#
def show_graphs():
    fig, axs = plt.subplots(2, 2, figsize=(15,12)) # axs is a (5,2) nd-array
    fig.suptitle('''Deterministic Model of sells only - varying number of 5-ETH-sells/day.
                 Target Liq of 2500 ETH and 4% liquidity movement/day resulting in 20 ETH injection.
                 Ratchet speed = 4%/day''', fontsize=16)
    fig.tight_layout()
    fig.subplots_adjust(top=0.9)
    # Subplot
    for i in range(len(sims)):
        axs[0, 0].plot(range(days[i]+1), sims[i].nxm_price_prediction, label=label_names[i])
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[0, 1].plot(range(days[i]+1), sims[i].nxm_supply_prediction, label=label_names[i])
    axs[0, 1].set_title('nxm_supply')
    axs[0, 1].legend()
    # Subplot
    for i in range(len(sims)):
        axs[1, 0].plot(range(days[i]+1), sims[i].book_value_prediction, label=label_names[i])
    axs[1, 0].set_title('book_value')
    axs[1, 0].set_ylim(top=0.08)
    axs[1, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[1, 1].plot(range(days[i]+1), sims[i].cap_pool_prediction, label=label_names[i])
    axs[1, 1].set_title('cap_pool')
    axs[1, 1].legend()
    # Subplot
    # for i in range(len(sims)):
    #     axs[2, 0].plot(range(days[i]+1), sims[i].liquidity_nxm_prediction, label=label_names[i])
    # axs[2, 0].set_title('liquidity_nxm')
    # axs[2, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[2, 1].plot(range(days[i]+1), sims[i].liquidity_eth_prediction, label=label_names[i])
    # axs[2, 1].plot(range(days[i]+1), np.full(shape=days[i]+1, fill_value=sys_params.target_liq))
    # axs[2, 1].set_title('liquidity_eth')
    # axs[2, 1].legend()
    # #Subplot
    # for i in range(len(sims)):
    #     axs[3, 0].plot(range(days[i]+1), sims[i].nxm_burned_prediction, label=label_names[i])
    # axs[3, 0].set_title('nxm_burned')
    # axs[3, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[3, 1].plot(range(days[i]+1), sims[i].nxm_minted_prediction, label=label_names[i])
    # axs[3, 1].set_title('nxm_minted')
    # axs[3, 1].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[4, 0].plot(range(days[i]+1), sims[i].eth_sold_prediction, label=label_names[i])
    # axs[4, 0].set_title('eth_sold')
    # axs[4, 0].legend()
    # # Subplot
    # for i in range(len(sims)):
    #     axs[4, 1].plot(range(days[i]+1), sims[i].eth_acquired_prediction, label=label_names[i])
    # axs[4, 1].set_title('eth_acquired')
    # axs[4, 1].legend()

    plt.show()


if __name__ == "__main__":

    # range of variables to test
    lambda_exits_range = [5, 10, 15, 20, 25, 30]

    # create sims and label names for graphs
    sims = []
    label_names = []
    days = []

    for exits in lambda_exits_range:
        model_params.det_exit_array = np.full(shape=model_days,
                                              fill_value=exits,
                                              dtype=int)

        sims.append(UniProtocolDet())
        label_names.append(f'{exits} exits')

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
