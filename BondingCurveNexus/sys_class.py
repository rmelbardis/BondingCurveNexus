import numpy as np

from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
'''

class NexusSystem:

    def __init__(self):

        # initiate model parameters
        self.current_day = 0
        self.
