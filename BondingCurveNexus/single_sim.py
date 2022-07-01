'''
Function for running a single simulation
'''

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from BondingCurveNexus.sys_class import NexusSystem
from BondingCurveNexus.model_params import model_days

if __name__ == "__main__":

    sim = NexusSystem()

    for i in tqdm(range(model_days)):
        sim.one_day_passes()

    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(7, 2, figsize=(15,27)) # axs is a (7,2) nd-array

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
    axs[1, 1].plot(range(model_days+1), sim.dca_prediction)
    axs[1, 1].set_title('dca')
    # Subplot
    axs[2, 0].plot(range(model_days+1), sim.book_value_prediction)
    axs[2, 0].set_title('book_value')
    # Subplot
    axs[2, 1].plot(range(model_days+1), sim.mcrp_prediction)
    axs[2, 1].plot(range(model_days+1), np.ones(model_days+1), color='red')
    axs[2, 1].set_title('mcrp')
    # Subplot
    axs[3, 0].plot(range(model_days+1), sim.wnxm_prediction)
    axs[3, 0].set_title('wnxm_price')
    # Subplot
    axs[3, 1].plot(range(model_days+1), sim.nxm_supply_prediction)
    axs[3, 1].set_title('nxm_supply')
    # Subplot
    axs[4, 0].plot(range(model_days+1), sim.premium_prediction)
    axs[4, 0].set_title('premium_income')
    # Subplot
    axs[4, 1].plot(range(model_days+1), sim.claim_prediction)
    axs[4, 1].set_title('claim_outgo')
    # Subplot
    axs[5, 0].plot(range(model_days+1), sim.exit_queue_eth_prediction)
    axs[5, 0].set_title('exit_queue_eth')
    # Subplot
    axs[5, 1].plot(range(model_days+1), sim.exit_queue_nxm_prediction)
    axs[5, 1].set_title('exit_queue_nxm')
    # Subplot
    axs[6, 0].plot(range(model_days+1), sim.num_exits_prediction)
    axs[6, 0].set_title('num_exits_in_queue')
    # Subplot
    axs[6, 1].plot(range(model_days+1), sim.investment_return_prediction)
    axs[6, 1].set_title('investment_return')

    plt.show()
