'''
Running a single deterministic simulation of the protocol buy/sell mechanism only:
 - buying from protocol
 - selling to protocol
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params, model_params
from BondingCurveNexus.HighLowCap.RAMM_HighLowCap_Protocol_det import RAMMHighLowCapProtocolDet
from BondingCurveNexus.model_params import model_days


#-----GRAPHS-----#
def show_graphs():
    # Destructuring initialization
    fig, axs = plt.subplots(3, 2, figsize=(15,18))
    fig.suptitle(f'''Deterministic Protocol-only Model
                 Opening liq of {sys_params.open_liq_sell} ETH and Target liq of {sys_params.target_liq_sell} ETH
                 {sys_params.liq_out_perc*100}% liquidity movement/day resulting in max of {sys_params.target_liq_buy*sys_params.liq_out_perc} ETH injection/withdrawal.
                 {model_params.lambda_entries} {model_params.det_entry_size}-ETH-entries/day resulting in {model_params.det_entry_size * model_params.lambda_entries} ETH/day
                 {model_params.lambda_exits} {model_params.det_NXM_exit}-NXM-exits/day resulting in {model_params.det_NXM_exit * model_params.lambda_exits} NXM/day
                 ''',
                 fontsize=16)
    # fig.tight_layout()
    fig.subplots_adjust(top=0.88)

    # Subplot
    axs[0, 0].plot(range(days_run+1), sim.spot_price_b_prediction, label='price below')
    axs[0, 0].plot(range(days_run+1), sim.spot_price_a_prediction, label='price above')
    axs[0, 0].plot(range(days_run+1), sim.book_value_prediction, label='book value')
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(range(days_run+1), sim.cap_pool_prediction)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].plot(range(days_run+1), sim.nxm_supply_prediction, label='nxm')
    axs[1, 0].set_title('nxm_supply')
    # Subplot
    axs[1, 1].plot(range(days_run+1), sim.liq_NXM_b_prediction, label='NXM reserve below')
    axs[1, 1].plot(range(days_run+1), sim.liq_NXM_a_prediction, label='NXM reserve above')
    axs[1, 1].set_title('liquidity_nxm')
    axs[1, 1].legend()
    # Subplot
    axs[2, 0].plot(range(days_run+1), sim.liq_prediction, label='ETH liquidity')
    axs[2, 0].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq_sell), label='target')
    axs[2, 0].set_title('liquidity_eth')
    axs[2, 0].legend()
    # # Subplot
    # axs[3, 0].plot(range(days_run+1), sim.nxm_burned_prediction)
    # axs[3, 0].set_title('nxm_burned')
    # # Subplot
    # axs[3, 1].plot(range(days_run+1), sim.nxm_minted_prediction)
    # axs[3, 1].set_title('nxm_minted')
    # # Subplot
    # axs[4, 0].plot(range(days_run+1), sim.eth_sold_prediction)
    # axs[4, 0].set_title('eth_sold')
    # # Subplot
    # axs[4, 1].plot(range(days_run+1), sim.eth_acquired_prediction)
    # axs[4, 1].set_title('eth_acquired')

    plt.show()


if __name__ == "__main__":

    # initial_days = 30
    # initial_daily_entries = 0

    # model_params.det_entry_array = np.empty(model_params.model_days, dtype=int)
    # model_params.det_entry_array[:initial_days] = initial_daily_entries
    # model_params.det_entry_array[initial_days:] = model_params.lambda_entries

    sim = RAMMHighLowCapProtocolDet()
    days_run = 0

    for i in tqdm(range(model_days)):
        try:
            sim.one_day_passes()
            days_run += 1
        except ZeroDivisionError:
            print('Something went to Zero!')
            break
