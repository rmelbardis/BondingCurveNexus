import numpy as np

from BondingCurveNexus.MovingTarget.RAMM_MovTar_Pools import RAMMMovTarPools
from BondingCurveNexus import model_params

class RAMMMovTarDet(RAMMMovTarPools):
    def __init__(self, daily_printout_day=0):

        # initialise all the same stuff as base class
        super().__init__(daily_printout_day)

        # base entries and exits using a fixed pre-defined array
        self.base_daily_platform_buys = model_params.det_entry_array
        self.base_daily_platform_sales = model_params.det_exit_array

    def nxm_sale_size(self):
        # standard deterministic size of nxm sales
        return model_params.det_exit_size / self.sell_nxm_price()

    def nxm_buy_size(self):
        # standard deterministic size of nxm sales
        return model_params.det_entry_size / self.buy_nxm_price()
