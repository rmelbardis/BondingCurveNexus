'''
Function for running a single simulation
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus.sys_class import NexusSystem
from BondingCurveNexus.model_params import model_days
from BondingCurveNexus.param_functions import open_liq, wnxm_movement_per_eth

if __name__ == "__main__":

    sim = NexusSystem(liquidity_eth=open_liq(0.5),
                      wnxm_move_size=wnxm_movement_per_eth(two_perc_liq_usd=500_000))

    for i in tqdm(range(model_days)):
        sim.one_day_passes()

    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(10, 2, figsize=(15,27)) # axs is a (10,2) nd-array

    # Subplot
    axs[0, 0].plot(range(model_days+1), sim.mcr_prediction)
    axs[0, 0].set_title('mcr')
    # Subplot
    axs[0, 1].plot(range(model_days+1), sim.cap_pool_prediction)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].plot(range(model_days+1), sim.act_cover_prediction)
    axs[1, 0].set_title('active_cover')
    # Subplot
    axs[1, 1].plot(range(model_days+1), sim.mcrp_prediction)
    axs[1, 1].plot(range(model_days+1), np.ones(model_days+1), color='red')
    axs[1, 1].set_title('mcrp')
    # Subplot
    axs[2, 0].plot(range(model_days+1), sim.nxm_price_prediction)
    axs[2, 0].set_title('nxm_price')
    # Subplot
    axs[2, 1].plot(range(model_days+1), sim.wnxm_price_prediction)
    axs[2, 1].set_title('wnxm_price')
    # Subplot
    axs[3, 0].plot(range(model_days+1), sim.liquidity_nxm_prediction)
    axs[3, 0].set_title('liquidity_nxm')
    # Subplot
    axs[3, 1].plot(range(model_days+1), sim.liquidity_eth_prediction)
    axs[3, 1].set_title('liquidity_eth')
    # Subplot
    axs[4, 0].plot(range(model_days+1), sim.nxm_supply_prediction)
    axs[4, 0].set_title('nxm_supply')
    # Subplot
    axs[4, 1].plot(range(model_days+1), sim.wnxm_supply_prediction)
    axs[4, 1].set_title('wnxm_supply')
    # Subplot
    axs[5, 0].plot(range(model_days+1), sim.book_value_prediction)
    axs[5, 0].set_title('book_value')
    # Subplot
    axs[5, 1].plot(range(model_days+1), sim.cum_premiums_prediction)
    axs[5, 1].set_title('cum_premiums')
    # Subplot
    axs[6, 0].plot(range(model_days+1), sim.cum_claims_prediction)
    axs[6, 0].set_title('cum_claims')
    # Subplot
    axs[6, 1].plot(range(model_days+1), sim.cum_investment_prediction)
    axs[6, 1].set_title('cum_investment')
    # Subplot
    axs[7, 0].plot(range(model_days+1), sim.eth_sold_prediction)
    axs[7, 0].set_title('eth_sold')
    # Subplot
    axs[7, 1].plot(range(model_days+1), sim.eth_acquired_prediction)
    axs[7, 1].set_title('eth_acquired')
    # Subplot
    axs[8, 0].plot(range(model_days+1), sim.nxm_burned_prediction)
    axs[8, 0].set_title('nxm_burned')
    # Subplot
    axs[8, 1].plot(range(model_days+1), sim.nxm_minted_prediction)
    axs[8, 1].set_title('nxm_minted')
    # Subplot
    axs[9, 0].plot(range(model_days+1), sim.wnxm_removed_prediction)
    axs[9, 0].set_title('wnxm_removed')
    # Subplot
    axs[9, 1].plot(range(model_days+1), sim.wnxm_created_prediction)
    axs[9, 1].set_title('wnxm_created')

    plt.show()
