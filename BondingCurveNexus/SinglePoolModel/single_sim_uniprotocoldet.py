'''
Running a single deterministic simulation of the protocol buy/sell mechanism only:
 - buying from protocol
 - selling to protocol
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params, model_params
from BondingCurveNexus.uni_protocol_det import UniProtocolDet
from BondingCurveNexus.model_params import model_days


#-----GRAPHS-----#
def show_graphs():
    # Destructuring initialization
    fig, axs = plt.subplots(5, 2, figsize=(15,27))
    fig.suptitle(f'''Deterministic Model - {model_params.lambda_entries / model_params.lambda_exits} ratio of buys/sales
                 Opening Liq of {sys_params.open_liq_sell} ETH and Target Liq of {sys_params.target_liq_sell} ETH
                 {sys_params.liq_out_perc*100}% liquidity movement/day resulting in max of {sys_params.target_liq_buy*sys_params.liq_out_perc} ETH injection/withdrawal.
                 {model_params.lambda_entries} {model_params.det_entry_size}-ETH-entries/day resulting in {model_params.det_entry_size * model_params.lambda_entries} ETH/day
                 ''',
                 fontsize=16)
    fig.tight_layout()
    fig.subplots_adjust(top=0.93)

    # Subplot
    axs[0, 0].plot(range(days_run+1), sim.nxm_price_prediction)
    axs[0, 0].set_title('nxm_price')
    # Subplot
    axs[0, 1].plot(range(days_run+1), sim.book_value_prediction)
    axs[0, 1].set_title('book_value')
    # Subplot
    axs[1, 0].plot(range(days_run+1), sim.cap_pool_prediction)
    axs[1, 0].set_title('cap_pool')
    # Subplot
    axs[1, 1].plot(range(days_run+1), sim.nxm_supply_prediction)
    axs[1, 1].set_title('nxm_supply')
    # Subplot
    axs[2, 0].plot(range(days_run+1), sim.liquidity_nxm_prediction)
    axs[2, 0].set_title('liquidity_nxm')
    # Subplot
    axs[2, 1].plot(range(days_run+1), sim.liquidity_eth_prediction)
    axs[2, 1].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq_sell))
    axs[2, 1].set_title('liquidity_eth')
    # Subplot
    axs[3, 0].plot(range(days_run+1), sim.nxm_burned_prediction)
    axs[3, 0].set_title('nxm_burned')
    # Subplot
    axs[3, 1].plot(range(days_run+1), sim.nxm_minted_prediction)
    axs[3, 1].set_title('nxm_minted')
    # Subplot
    axs[4, 0].plot(range(days_run+1), sim.eth_sold_prediction)
    axs[4, 0].set_title('eth_sold')
    # Subplot
    axs[4, 1].plot(range(days_run+1), sim.eth_acquired_prediction)
    axs[4, 1].set_title('eth_acquired')

    plt.show()


if __name__ == "__main__":

    sim = UniProtocolDet(daily_printout_day=50)
    days_run = 0

    for i in tqdm(range(model_days)):
        try:
            sim.one_day_passes()
            days_run += 1
        except ZeroDivisionError:
            print('Something went to Zero!')
            break
