'''
Function for running a multiple simulations
'''

import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm

from BondingCurveNexus.sys_class import NexusSystem
from BondingCurveNexus.model_params import model_days

# if __name__ == "__main__":

def multi_sim():

    # define number of sims and initialise number of instances
    num_sims = 100
    sims = [NexusSystem() for x in range(num_sims)]

    # loop through individual instances and number of days for each simulation
    for sim in tqdm(sims):
        for i in range(model_days):
            sim.one_day_passes()

    #-----RESULT VISUALISATION-----#
    # Final outcome arrays
    final_mcr_list = [sim.mcr_prediction[-1] for sim in sims]
    final_cap_pool_list = [sim.cap_pool_prediction[-1] for sim in sims]
    final_eth_exit_list = [sim.exit_queue_eth_prediction[-1] for sim in sims]
    final_nxm_exit_list = [sim.exit_queue_nxm_prediction[-1] for sim in sims]
    final_dca_list = [sim.dca_prediction[-1] for sim in sims]
    final_book_value_list = [sim.book_value_prediction[-1] for sim in sims]
    final_mcrp_list = [sim.mcrp_prediction[-1] for sim in sims]
    final_wnxm_list = [sim.wnxm_prediction[-1] for sim in sims]
    final_nxm_supply_list = [sim.nxm_supply_prediction[-1] for sim in sims]
    final_premium_list = [sim.premium_prediction[-1] for sim in sims]
    final_claim_list = [sim.claim_prediction[-1] for sim in sims]
    final_act_cover_list = [sim.act_cover_prediction[-1] for sim in sims]
    final_num_exits_list = [sim.num_exits_prediction[-1] for sim in sims]
    final_investment_list = [sim.investment_return_prediction[-1] for sim in sims]

    #-----HISTOGRAMS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(7, 2, figsize=(15,27)) # axs is a (7,2) nd-array

    # Subplot
    axs[0, 0].hist(final_mcr_list, bins=25)
    axs[0, 0].set_title('mcr')
    # Subplot
    axs[0, 1].hist(final_cap_pool_list, bins=25)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].hist(final_act_cover_list, bins=25)
    axs[1, 0].set_title('active_cover')
    # Subplot
    axs[1, 1].hist(final_dca_list, bins=25)
    axs[1, 1].set_title('dca')
    # Subplot
    axs[2, 0].hist(final_book_value_list, bins=25)
    axs[2, 0].set_title('book_value')
    # Subplot
    axs[2, 1].hist(final_mcrp_list, bins=25)
    axs[2, 1].set_xbound(lower=0.0, upper=10.0)
    axs[2, 1].set_title('mcrp')
    # Subplot
    axs[3, 0].hist(final_wnxm_list, bins=25)
    axs[3, 0].set_title('wnxm_price')
    # Subplot
    axs[3, 1].hist(final_nxm_supply_list, bins=25)
    axs[3, 1].set_title('nxm_supply')
    # Subplot
    axs[4, 0].hist(final_premium_list, bins=25)
    axs[4, 0].set_title('premium_income')
    # Subplot
    axs[4, 1].hist(final_claim_list, bins=25)
    axs[4, 1].set_title('claim_outgo')
    # Subplot
    axs[5, 0].hist(final_eth_exit_list, bins=25)
    axs[5, 0].set_title('exit_queue_eth')
    # Subplot
    axs[5, 1].hist(final_nxm_exit_list, bins=25)
    axs[5, 1].set_title('exit_queue_nxm')
    # Subplot
    axs[6, 0].hist(final_num_exits_list, bins=25)
    axs[6, 0].set_title('num_exits_in_queue')
    # Subplot
    axs[6, 1].hist(final_investment_list, bins=25)
    axs[6, 1].set_title('investment_return')

    plt.show()
