'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time.
'''

import numpy as np

from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

class NexusSystem:

    def __init__(self):
        # opening state of system upon initializing a projection instance
        self.current_day = 0
        self.act_cover = sys_params.act_cover_now
        self.nxm_supply = sys_params.nxm_supply_now
        self.cap_pool = sys_params.cap_pool_now
        self.exit_array = np.zeros((1, model_params.model_days +
                                        sys_params.base_exit_days +
                                        sys_params.mcrp_max_days +
                                        sys_params.queue_max_days +
                                        sys_params.option_exit_period
                                    ))
        self.entry_array = np.zeros((1, model_params.model_days +
                                     sys_params.entry_bond_length
                                    ))

    # instance functions to calculate a variety of ongoing metrics
    def mcr(self):
        return self.act_cover / sys_params.capital_factor

    def mcrp(self, capital):
        return capital/self.mcr()

    def book_value(self, capital):
        return capital/self.nxm_supply

    def exit_queue_size(self, denom='eth'):
        nxm_in_queue = np.sum(np.amax(self.exit_array, axis=1))
        if denom == 'nxm':
            return nxm_in_queue
        return self.book_value(self.cap_pool) * nxm_in_queue

    def dca(self):
        return self.cap_pool - self.exit_queue_size()
