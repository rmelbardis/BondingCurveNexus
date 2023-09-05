'''
Running a set number of single deterministic simulations of buying only:

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
    fig.suptitle(f'''Deterministic Model of buys only - varying ratchet speeds.
                 Opening Liq of {sys_params.open_liq_buy} ETH and Target Liq of {sys_params.target_liq_buy} ETH
                 {sys_params.liq_out_perc*100}% liquidity movement/day resulting in max of {sys_params.target_liq_buy*sys_params.liq_out_perc} ETH withdrawal.
                 {model_params.lambda_entries} {model_params.det_entry_size}-ETH-entries/day resulting in {model_params.det_entry_size * model_params.lambda_entries} ETH/day''', fontsize=16)
    fig.tight_layout(w_pad=2, h_pad=2)
    fig.subplots_adjust(top=0.88)
    # Subplot
    for i in range(len(sims)):
        axs[0, 0].plot(range(days[i]+1), sims[i].nxm_price_prediction, label=label_names[i])
    axs[0, 0].set_title('nxm_price')
    # axs[0, 0].set_ylim(top=0.2, bottom=0)
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
    # axs[1, 0].set_ylim(top=0.08, bottom=0)
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
    # axs[2, 0].set_ylim(top=4e5, bottom=0)
    axs[2, 0].legend()
    # Subplot
    for i in range(len(sims)):
        axs[2, 1].plot(range(days[i]+1), sims[i].liquidity_eth_prediction, label=label_names[i])
    axs[2, 1].plot(range(days[i]+1), np.full(shape=days[i]+1, fill_value=sys_params.target_liq_buy))
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
    ratchet_range = [0.035, 0.04, 0.045]

    # create empty lists of sims and label names for graphs
    sims = []
    label_names = []
    days = []

    # create sim & label list
    for speed in ratchet_range:
        sims.append(UniProtocolDet())
        label_names.append(f'{speed*100}% of BV/day')

    # loop through sim list while changing variables
    for n, sim in enumerate(sims):

        days_run = 0
        sys_params.ratchet_down_perc = ratchet_range[n]

        for i in tqdm(range(model_days)):
            try:
                sim.one_day_passes()
                days_run += 1
            except ZeroDivisionError:
                print('Something went to Zero!')
                break
        days.append(days_run)
