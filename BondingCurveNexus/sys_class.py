from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
'''

daily_investment_return: (1+investment_apy)**(1/365) - 1

class NexusSystem:

    # SYSTEM PARAMETERS - CURRENT FIXED BUT MAY BE SUBJECT TO CHANGE #
    system_vals = sys_params.dictionary
    model_vals = model_params.dictionary


    def __init__(self):

        # initiate model parameters
        self.current_day = 0
