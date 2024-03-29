import numpy as np

from BondingCurveNexus.HighLowCap.RAMM_HighLowCap_Protocol import RAMMHighLowCapProtocol
from BondingCurveNexus import model_params

class RAMMHighLowCapProtocolDet(RAMMHighLowCapProtocol):
    def __init__(self, daily_printout_day=0):

        # initialise all the same stuff as RAMM_HighLowCap_Protocol
        super().__init__(daily_printout_day)

        # base entries and exits using a fixed pre-defined array
        self.base_daily_protocol_buys = model_params.det_entry_array
        self.base_daily_protocol_sales = model_params.det_exit_array

    def nxm_sale_size(self):
        # standard deterministic size of nxm sales
        # return model_params.det_exit_size / self.spot_price_b()
        return model_params.det_NXM_exit

    def nxm_buy_size(self):
        # standard deterministic size of nxm buys
        return model_params.det_entry_size / self.spot_price_a()
