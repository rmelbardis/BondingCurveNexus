'''
Running a single deterministic simulation of the protocol buy/sell mechanism only:
 - buying from protocol
 - selling to protocol
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus import sys_params, model_params
from BondingCurveNexus.RAMM_markets_stoch import RAMMMarketsStoch
from BondingCurveNexus.model_params import model_days


#-----GRAPHS-----#
def show_graphs():
    # Destructuring initialization
    fig, axs = plt.subplots(6, 2, figsize=(15,27))
    fig.suptitle(f'''Stochastic Model
                 Opening buy liq of {sys_params.open_liq_buy} ETH and Target buy liq of {sys_params.target_liq_buy} ETH
                 Opening sell liq of {sys_params.open_liq_sell} ETH and Target sell liq of {sys_params.target_liq_sell} ETH
                 {sys_params.liq_out_perc*100}% liquidity movement/day resulting in max of {sys_params.target_liq_buy*sys_params.liq_out_perc} ETH injection/withdrawal.
                 Mean {model_params.lambda_entries} 4.3-ETH-entries/day
                 Mean {model_params.lambda_exits} 4.3-ETH-exits/day
                 ''')
    fig.tight_layout()
    fig.subplots_adjust(top=0.92)

    # Subplot
    axs[0, 0].plot(range(days_run+1), sim.sell_nxm_price_prediction, label='sell price')
    axs[0, 0].plot(range(days_run+1), sim.buy_nxm_price_prediction, label='buy price')
    axs[0, 0].plot(range(days_run+1), sim.wnxm_price_prediction, label='wnxm price')
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(range(days_run+1), sim.book_value_prediction)
    axs[0, 1].set_title('book_value')
    # Subplot
    axs[1, 0].plot(range(days_run+1), sim.cap_pool_prediction)
    axs[1, 0].set_title('cap_pool')
    # Subplot
    axs[1, 1].plot(range(days_run+1), sim.nxm_supply_prediction, label='nxm')
    axs[1, 1].plot(range(days_run+1), sim.wnxm_supply_prediction, label='wnxm')
    axs[1, 1].set_title('nxm_supply')
    # Subplot
    axs[2, 0].plot(range(days_run+1), sim.sell_liquidity_nxm_prediction, label='sell liquidity')
    axs[2, 0].plot(range(days_run+1), sim.buy_liquidity_nxm_prediction, label='buy liquidity')
    axs[2, 0].set_title('liquidity_nxm')
    axs[2, 0].legend()
    # Subplot
    axs[2, 1].plot(range(days_run+1), sim.sell_liquidity_eth_prediction, label='sell liquidity')
    axs[2, 1].plot(range(days_run+1), sim.buy_liquidity_eth_prediction, label='buy liquidity')
    axs[2, 1].plot(range(days_run+1), np.full(shape=days_run+1, fill_value=sys_params.target_liq_sell), label='target')
    axs[2, 1].set_title('liquidity_eth')
    axs[2, 1].legend()
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
    # Subplot
    axs[5, 0].plot(range(days_run+1), sim.wnxm_removed_prediction)
    axs[5, 0].set_title('wnxm_removed')
    # Subplot
    axs[5, 1].plot(range(days_run+1), sim.wnxm_created_prediction)
    axs[5, 1].set_title('wnxm_created')

    plt.show()


if __name__ == "__main__":

    sim = RAMMMarketsStoch()
    days_run = 0

    for i in tqdm(range(model_days)):
        try:
            sim.one_day_passes()
            days_run += 1
        except ZeroDivisionError:
            print('Something went to Zero!')
            break
