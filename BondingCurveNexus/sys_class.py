'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
in a consistent manner.
'''
from scipy.stats import lognorm
import numpy as np

from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

class NexusSystem:

    def __init__(self):
        # OPENING STATE of system upon initializing a projection instance
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
        self.wnxm_price = sys_params.wnxm_price_now

        # set cumulative counters to zero
        self.cum_premiums = 0
        self.cum_claims = 0
        self.cum_investment = 0

        # create RANDOM VARIABLE ARRAYS for individual projection
        # base entries and exits using a poisson distribution
        self.daily_entries = np.random.poisson(lam=model_params.lambda_entries,
                                                size=model_params.model_days)
        self.daily_exits = np.random.poisson(lam=model_params.lambda_exits,
                                                size=model_params.model_days)

        # base premium daily incomes using a lognormal distribution
        self.daily_premiums = lognorm.rvs(s=model_params.premium_shape,
                                          loc=model_params.premium_loc,
                                          scale=model_params.premium_scale,
                                          size=model_params.model_days)

    # INSTANCE FUNCTIONS to calculate a variety of ongoing metrics & parameters
    # and update the system

    # calculate mcr from current cover amount
    def mcr(self):
        return self.act_cover / sys_params.capital_factor

    # calculate mcr% from current assets and mcr size.
    # Specify whether to use all current assets or remove exit queue
    def mcrp(self, capital='pool'):
        if capital == 'dca':
            return self.dca()/self.mcr()
        return self.cap_pool/self.mcr()

    # calculate book value from current assets & nxm supply.
    def book_value(self):
        return self.cap_pool/self.nxm_supply

    # create function that calculates the size of the exit queue in NXM or ETH
    # current book value * notional number of NXM in the exit queue
    # (sum of maximum of each row)
    def exit_queue_size(self, denom='eth'):
        nxm_in_queue = np.sum(np.amax(self.exit_array, axis=1))
        if denom == 'nxm':
            return nxm_in_queue
        return self.book_value() * nxm_in_queue

    # Dynamic Current Assets - capital pool less exit queue
    def dca(self):
        return self.cap_pool - self.exit_queue_size()

    # premium & claim scaling based on active cover
    def prem_claim_scaler(self):
        return self.act_cover / sys_params.act_cover_now

    # Bond bonus calculation, based on MCR% after allowing for exit queue
    # Function with upper limit on exponent, parameterised
    def bond_bonus(self):
        return sys_params.entry_bond_max_interest * (1 - np.exp(
                                                    -sys_params.entry_bond_shape *
                                                    self.mcrp(capital='dca')
                                                    )
                                                    )

    # mcrp days added linearly based on mcr% parameters
    def mcrp_exit_days(self):
        return sys_params.mcrp_max_days * min(1,
                                        max(0,
                                        (sys_params.mcrp_trigger - self.mcrp(capital='dca')) /
                                        (sys_params.mcrp_trigger - sys_params.mcrp_threshold)
                                        ))

    # queue days added linearly based on exit queue size relative to nxm supply
    def queue_exit_days(self):
        queue_ratio = self.exit_queue_size(denom='nxm') / self.nxm_supply
        return sys_params.queue_max_days * min(1,
                                        max(0,
                                        (queue_ratio - sys_params.queue_trigger) /
                                        (sys_params.queue_threshold - sys_params.queue_trigger)
                                        ))

    # create numpy row vector of nxm received with bonus at appropriate time
    # and append it to entry array
    # update parameters of system
    def single_entry(self, eth):
        # work out number of nxm user could receive instantly (floor of book value)
        nxm_obtained = eth / max(self.book_value(), self.wnxm_price)

        # if mCR% < 1, encourage entries through bond interest
        if self.mcrp(capital='dca') < 1:
            # create empty row vector of maximum length
            row_vec = np.zeros(model_params.model_days + sys_params.entry_bond_length)
            # add bonus interest to instant nxm value
            nxm_obtained = nxm_obtained * (1 + max(0, self.bond_bonus()))
            # place value in appropriate time in row vector
            row_vec[self.current_day + sys_params.entry_bond_length] = nxm_obtained
            # append vector to entry array
            self.entry_array = np.vstack((self.entry_array, row_vec))
            # increase capital pool and number of nxm

        self.cap_pool += eth
        self.nxm_supply += nxm_obtained

        return self

    # create numpy row vector reflecting the possibilities of exit
    # including 0 for first 14 days
    # instant 100% after 14 days if mcrp > 1 and moving up curve to 100% if not
    def single_exit(self, eth):
        # set up single empty row vector of maximum possible length
        row_vec = np.zeros(model_params.model_days + sys_params.base_exit_days +
                           sys_params.mcrp_max_days + sys_params.queue_max_days +
                           sys_params.option_exit_period)

        # determine the first day user can exit from today
        start_day = self.current_day + sys_params.minimum_exit_period
        # if mcr% > 100%, user has option to exit after minimum waiting period
        # at full book value for 30 days
        if self.mcrp(capital='dca') > 1:
            ratio_array = np.ones(sys_params.option_exit_period)
            # replace relevant days with ones in array
            row_vec[start_day:start_day + sys_params.option_exit_period]

        # below 100% mcr
        else:
            # determine number of days to get to 100% book value
            days = np.ceil(sys_params.base_exit_days +
                           self.mcrp_exit_days() +
                           self.queue_exit_days()).astype('int')
            # combine the moving day target to 100% with a quadratic function to 100%
            ratio_array = np.minimum(
                            np.fromfunction(lambda x: (x/days)**2,
                                            (days + sys_params.option_exit_period,)),
                            1)
            # replace first 14 days with zero
            ratio_array[:sys_params.minimum_exit_period] = 0
            # replace array of zeros with ratio array in appropriate position
            row_vec[self.current_day:self.current_day + days +
                    sys_params.option_exit_period] = ratio_array

        # Converts desired ETH amount into nxm at book value (based on current capital)
        # in practice the users will choose NXM amount they want to sell
        # nxm value row represent the amount that the user gets relative to book value
        # in practice user will always burn the full amount of NXM
        nxm = eth/self.book_value()

        # multiply nxm values into row vector
        row_vec = row_vec * nxm

        # append vector to exit array
        self.exit_array = np.vstack((self.exit_array, row_vec))

        return self

    def wnxm_shift(self):
        self.wnxm_price *= (1 + np.random.normal(loc=model_params.wnxm_drift,
                                                scale=model_params.wnxm_diffusion)
                            )
        return self
