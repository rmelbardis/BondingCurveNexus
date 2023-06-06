import numpy as np
from scipy.stats import lognorm

from BondingCurveNexus.MovingTarget.RAMM_MovTar_Markets import RAMMMovTarMarkets
from BondingCurveNexus import model_params

class RAMMMovTarMarketsStoch(RAMMMovTarMarkets):
    def __init__(self, daily_printout_day=0):

        # initialise all the same stuff as RAMMMovTarMarkets
        super().__init__(daily_printout_day)

        # base entries and exits using a poisson distribution
        self.base_daily_platform_buys = np.random.poisson(
                                                lam=model_params.lambda_entries,
                                                size=model_params.model_days)
        self.base_daily_platform_sales = np.random.poisson(
                                                lam=model_params.lambda_exits,
                                                size=model_params.model_days)

    def nxm_sale_size(self):
        # lognormal distribution of nxm sales
        return lognorm.rvs(s=model_params.exit_shape,
                           loc=model_params.exit_loc,
                           scale=model_params.exit_scale) / self.sell_nxm_price()

    def nxm_buy_size(self):
        # lognormal distribution of nxm buys
        return lognorm.rvs(s=model_params.entry_shape,
                           loc=model_params.entry_loc,
                           scale=model_params.entry_scale) / self.buy_nxm_price()

    def wnxm_shift(self):
        # set percentage changes in wnxm price using a normal distribution
        self.wnxm_price *=  (1 + np.random.normal(loc=model_params.wnxm_drift,
                                                 scale=model_params.wnxm_diffusion)
                            )
