'''
Running a set number of single deterministic simulations of selling only:

 The purpose of this type of simulation is to test a range of parameters.
 Deterministic outcomes than then be compared to assess impact of varying this parameter.
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus.uni_protocol_det import UniProtocolDet
from BondingCurveNexus import model_params, sys_params
from BondingCurveNexus.model_params import model_days

#-----GRAPHS-----#
def show_graphs():
    fig, axs = plt.subplots(3, 2, figsize=(15,18)) # axs is a (5,2) nd-array
    fig.suptitle('''Deterministic Model of sells only - varying target liquidity.
                 Opening Liq equal to Target Liq. Ratchet = 4% of Book Value/day
                 Varied Liquidity movement/day resulting in 100 ETH injection.
                 Sell pressure = 100 ETH/day''', fontsize=16)
    fig.tight_layout(w_pad=2, h_pad=2)
    fig.subplots_adjust(top=0.88)
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
    axs[1, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[1, 1].plot(range(days[i]+1), sims[i].cap_pool_prediction, label=label_names[i])
    axs[1, 1].set_title('cap_pool')
    axs[1, 1].legend()
    # Subplot
    for i in range(len(sims)):
        axs[2, 0].plot(range(days[i]+1), sims[i].liquidity_nxm_prediction, label=label_names[i])
    axs[2, 0].set_title('liquidity_nxm')
    axs[2, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[2, 1].plot(range(days[i]+1), sims[i].liquidity_eth_prediction, label=label_names[i])
    # axs[2, 1].plot(range(days[i]+1), np.full(shape=days[i]+1, fill_value=sys_params.target_liq))
    axs[2, 1].set_title('liquidity_eth')
    axs[2, 1].legend()
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
    target_liq_range = [1000, 2500, 5000, 10_000, 20_000]
    liq_in_range = [0.1, 0.04, 0.02, 0.01, 0.005]

    # create sims and label names for graphs
    sims = []
    label_names = []
    days = []

    for liq in target_liq_range:
        # sys_params.open_liq = liq
        sys_params.target_liq = liq
        sims.append(UniProtocolDet())
        label_names.append(f'Target ETH Liquidity = {liq}')

    for n, sim in enumerate(sims):

        sys_params.liq_in_perc = liq_in_range[n]
        days_run = 0

        for i in tqdm(range(model_days)):
            try:
                sim.one_day_passes()
                days_run += 1
            except ZeroDivisionError:
                print('Something went to Zero!')
                break
        days.append(days_run)
