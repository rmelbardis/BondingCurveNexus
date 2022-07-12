'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
in a consistent manner.
'''
from scipy.stats import lognorm
import numpy as np
from random import random, shuffle

from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

class NexusSystem:

    def __init__(self):
        # OPENING STATE of system upon initializing a projection instance
        self.current_day = 0
        self.act_cover = sys_params.act_cover_now
        self.nxm_supply = sys_params.nxm_supply_now
        self.cap_pool = sys_params.cap_pool_now

        # exit array will only be day of exit, ratio of exit,
        # number of nxm & whether exit actually happened
        self.exit_array = np.zeros((1, 4))
        # ENTRY ARRAY NOT USED CURRENTLY #
        # self.entry_array = np.zeros((1, model_params.model_days +
        #                              sys_params.entry_bond_length
        #                             ))
        self.wnxm_price = sys_params.wnxm_price_now

        # set cumulative counters to zero
        self.cum_premiums = 0
        self.cum_claims = 0
        self.cum_investment = 0

        # create RANDOM VARIABLE ARRAYS for individual projection
        # base entries and exits using a poisson distribution
        self.base_daily_entries = np.random.poisson(
                                                lam=model_params.lambda_entries,
                                                size=model_params.model_days)
        self.base_daily_exits = np.random.poisson(
                                                lam=model_params.lambda_exits,
                                                size=model_params.model_days)

        # base premium daily incomes using a lognormal distribution
        self.base_daily_premiums = lognorm.rvs(s=model_params.premium_shape,
                                          loc=model_params.premium_loc,
                                          scale=model_params.premium_scale,
                                          size=model_params.model_days)

        # daily percentage changes in cover amount and wnxm price using a normal distribution
        self.base_daily_cover_change = np.random.normal(
                                            loc=model_params.cover_amount_mean,
                                            scale=model_params.cover_amount_stdev,
                                            size = model_params.model_days
                                            )
        self.base_daily_wnxm_change = np.random.normal(
                                            loc=model_params.wnxm_drift,
                                            scale=model_params.wnxm_diffusion,
                                            size = model_params.model_days)

        # daily randomised values between 0 and 1 to check vs claim occurence probability
        self.claim_rolls = np.random.random(size = model_params.model_days)

        # create tracking lists for individual instance
        self.mcr_prediction = [self.mcr()]
        self.cap_pool_prediction = [self.cap_pool]
        self.mcrp_prediction = [self.mcrp(self.dca())]
        self.wnxm_prediction = [self.wnxm_price]
        self.nxm_supply_prediction = [self.nxm_supply]
        self.book_value_prediction = [self.book_value()]
        self.exit_queue_eth_prediction = [self.exit_queue_size()]
        self.exit_queue_nxm_prediction = [self.exit_queue_size(denom='nxm')]
        self.dca_prediction = [self.dca()]
        self.premium_prediction = [0]
        self.act_cover_prediction = [self.act_cover]
        self.claim_prediction = [0]
        self.investment_return_prediction = [0]
        self.num_exits_prediction = [0]

    # INSTANCE FUNCTIONS
    # to calculate a variety of ongoing metrics & parameters
    # and update the system accordingly

    # calculate mcr from current cover amount
    # minimum of 0.01 ETH to avoid division by zero
    def mcr(self):
        return max(0.01, self.act_cover / sys_params.capital_factor)

    # calculate mcr% from current assets and mcr size.
    # Specify whether to use all current assets or remove exit queue
    def mcrp(self, capital):
        return min(20, capital/self.mcr())

    # calculate book value from current assets & nxm supply.
    def book_value(self):
        if self.nxm_supply == 0:
            return 0
        return self.cap_pool/self.nxm_supply

    # create function that calculates the size of the exit queue in NXM or ETH
    # current book value * notional number of NXM in the exit queue
    # (sum of maximum of each row)
    def exit_queue_size(self, denom='eth'):
        nxm_in_queue = np.sum(self.exit_array[:, -1])
        if denom == 'nxm':
            return nxm_in_queue
        return self.book_value() * nxm_in_queue

    # Dynamic Current Assets - capital pool less exit queue
    def dca(self):
        return self.cap_pool - self.exit_queue_size()

    # Bond bonus calculation, based on MCR% after allowing for exit queue
    # Function with upper limit on exponent, parameterised
    def bond_bonus(self):
        return sys_params.entry_bond_max_interest * (1 - np.exp(
                                                    -sys_params.entry_bond_shape *
                                                    (1 - self.mcrp(self.dca()))
                                                    )
                                                    )

    # mcrp days added linearly based on mcr% parameters
    def mcrp_exit_days(self):
        return sys_params.mcrp_max_days * min(1,
                                        max(0,
                                        (sys_params.mcrp_trigger - self.mcrp(self.dca())) /
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

    # update parameters of system upon single entry
    # includes instant entries above 100% MCR% and bond entries below
    def single_entry(self, eth):
        # work out number of nxm user could receive instantly (floor of book value)
        nxm_obtained = eth / max(self.book_value(), self.wnxm_price)

        # if MCR% < 1, encourage entries through bond interest
        # not currently using array
        if self.mcrp(self.dca()) < 1:
            # # create empty row vector of maximum length
            # row_vec = np.zeros(model_params.model_days + sys_params.entry_bond_length)

            # add bonus interest to instant nxm value
            nxm_obtained = nxm_obtained * (1 + max(0, self.bond_bonus()))

            # # place value in appropriate time in row vector
            # row_vec[self.current_day + sys_params.entry_bond_length] = nxm_obtained
            # # append vector to entry array
            # self.entry_array = np.vstack((self.entry_array, row_vec))
            # increase capital pool and number of nxm

        self.cap_pool += eth
        self.nxm_supply += nxm_obtained

    # create numpy row vector reflecting exit day, ratio of book and number of nxm
    # including 0 for first 14 days
    # instant 100% after 14 days if mcrp > 1 and moving up curve to 100% if not
    def single_exit(self, eth):
        # set up single empty row vector of length 4 to track exits
        # columns are:
        # flag for successful exit --- day of exit --- ratio of book --- nxm amount
        row_vec = np.zeros(4)

        # determine the first day user can exit after minimum period
        start_day = self.current_day + sys_params.minimum_exit_period

        # check whether exit happens at all (at certain probability)
        # successful exit
        if np.random.random() <= model_params.p_exit:
            # flag that exit happens
            row_vec[0] = 1
        else:
            # flag that exit doesn't happen
            row_vec[0] = 0

        # if mcr% > 100%, user has option to exit after minimum waiting period
        # at full book value for 30 days
        if self.mcrp(self.dca()) > 1:
            # ratio of exit will always be 1 here
            row_vec[2] = 1
            # check whether user will actually exit
            if row_vec[0] == 1:
                # randomise day & add to current day, place in column
                full_exit_day = np.random.randint(0, sys_params.option_exit_period)
                row_vec[1] = start_day + full_exit_day
            else:
                # option drops off after 30 days
                row_vec[1] = start_day + sys_params.option_exit_period

        # below 100% mcr
        else:
            # determine number of days to get to 100% book value
            days_to_full = np.ceil(sys_params.base_exit_days +
                           self.mcrp_exit_days() +
                           self.queue_exit_days()).astype('int')

            # check whether user will actually exit
            if row_vec[0] == 1:
                # check whether user exits at full book
                if np.random.random() <= model_params.p_exit_full_bv:
                    # if true, exit is at full book value
                    row_vec[2] = 1
                    # randomise exit day from 30 available
                    full_exit_day = np.random.randint(0, sys_params.option_exit_period)
                    row_vec[1] = self.current_day + days_to_full + full_exit_day
                # if not, construct ratios and determine exit time & value
                else:
                    # combine the moving day target to 100% with a quadratic function to 100%
                    # creates possible exit ratios on different days
                    ratio_vector = np.fromfunction(lambda x: (x/days_to_full)**2,(days_to_full,))
                    # find index of first value above threshold in ratio vector
                    threshold_idx = np.where(ratio_vector > model_params.exit_bv_threshold)[0][0]

                    # check whether exit is above bv threshold
                    if np.random.random() <= model_params.p_exit_above_threshold:
                        # select random value between threshold and days to full bv
                        exit_day = np.random.randint(threshold_idx, days_to_full)
                        row_vec[1] = self.current_day + exit_day
                        row_vec[2] = ratio_vector[exit_day]
                    # exit below threshold
                    else:
                        exit_day = np.random.randint(sys_params.minimum_exit_period, threshold_idx)
                        row_vec[1] = self.current_day + exit_day
                        row_vec[2] = ratio_vector[exit_day]
            else:
                # option drops off after days + 30 & doesn't matter what ratio is
                row_vec[1] = start_day + days_to_full + sys_params.option_exit_period


        # Converts desired ETH amount into nxm at book value (based on current capital)
        # in practice the users will choose NXM amount they want to sell
        # nxm value row represent the amount that the user gets relative to book value
        # in practice user will always burn the full amount of NXM
        nxm = min(eth/self.book_value(), self.nxm_supply)

        # place full nxm value in final position on row vector
        row_vec[3] = nxm

        # append vector to exit array
        self.exit_array = np.vstack((self.exit_array, row_vec))

    # eth sizer - throttle size of sale if pushing up against limits
    def eth_sale_size(self, eth):
        # if mcr% > 100%,
        # check whether size reduces mcrp below 1 & turn eth_size into maximum possible
        # such that mcrp doesn't go below 1
        if self.mcrp(self.dca()) > 1:
            if self.mcrp(self.dca() - eth) <= 1:
                eth = self.dca() - self.mcr()

        # don't allow size of exit queue in eth to go above capital pool size
        if self.exit_queue_size(denom='eth') + eth > self.cap_pool:
            eth = self.cap_pool - self.exit_queue_size(denom='eth')

        # don't allow size of exit queue in nxm to go above nxm supply
        # throttle eth to available nxm * book value
        # (which then will get converted back to nxm value during the single_exit process)
        if self.exit_queue_size(denom='nxm') + eth/self.book_value() > self.nxm_supply:
            eth = (self.nxm_supply - self.exit_queue_size(denom='nxm')) * self.book_value()

        # don't allow sales for more than there is in the capital pool
        eth = min(eth, self.cap_pool)

        return eth

    # exits from exit queue in a single day
    def delayed_exits(self):
        # slice exit array to only have current day's values
        today_array = self.exit_array[self.exit_array[:, 1] == self.current_day]

        # deal with exits that don't happen
        today_remains = today_array[today_array[:, 0] == 0]
        # burn 10% of nxm value
        self.nxm_supply -= sys_params.option_cost * np.sum(today_remains[:, 3])

        # deal with exits that happen
        today_exits = today_array[today_array[:, 0] == 1]
        # burn nxm value (limit to 0)
        self.nxm_supply = max(self.nxm_supply - np.sum(today_exits[:, 3]), 0)
        # remove value of nxm from capital pool (limit to 0)
        self.cap_pool = max(0,
                        self.cap_pool - np.sum(today_exits[:, 2] * today_exits[:, 3])
                        * self.book_value())

        # remove today's exit rows from exit array
        self.exit_array = self.exit_array[self.exit_array[:, 1] != self.current_day]

    # daily percentage change in wNXM price
    def wnxm_shift(self):
        self.wnxm_price *= (1 + self.base_daily_wnxm_change[self.current_day])

    # daily percentage change in active cover amount
    def cover_amount_shift(self):
        # no buys allowed
        if (self.nxm_supply - self.exit_queue_size(denom='nxm')) *\
            sys_params.stake_ceil_factor < self.act_cover/self.wnxm_price:
            self.act_cover = max(0, self.act_cover - model_params.cover_amount_drop)

        # normal scenario
        else:
            self.act_cover *= (1 + self.base_daily_cover_change[self.current_day])

    # premium & claim scaling based on active cover vs opening active cover
    def act_cover_scaler(self):
        return self.act_cover / sys_params.act_cover_now

    # daily premium income and additions to nxm supply & cap pool
    # (scaled relative to active cover amount)
    # logged in cumulative premiums
    def premium_income(self):
        daily_premium = self.base_daily_premiums[self.current_day] *\
                        self.act_cover_scaler()
        self.cap_pool += daily_premium
        self.nxm_supply += 0.5 * daily_premium/self.wnxm_price
        self.cum_premiums += daily_premium

    # claim payout - checks whether there are claims and if there is
    # size is randomised using a lognormal distribution (scaled relative to active cover amount)
    # claim amount is removed from pool and 50% of corresponding staking nxm burnt
    # logged in cumulative claims
    def claim_payout(self):
        if self.claim_rolls[self.current_day] < model_params.claim_prob:
            claim_size = lognorm.rvs(s=model_params.claim_shape,
                                     loc=model_params.claim_loc,
                                     scale=model_params.claim_scale) *\
                            self.act_cover_scaler()

            self.nxm_supply = max(0, self.nxm_supply - 0.5 * claim_size/self.wnxm_price)
            self.nxm_supply += model_params.claim_ass_reward * claim_size/self.wnxm_price
            self.cap_pool = max(0, self.cap_pool - claim_size)
            self.cum_claims += claim_size

    # work out daily return on capital pool and add to cap pool and cumulative
    def investment_return(self):
        inv_return = model_params.daily_investment_return * self.cap_pool
        self.cap_pool += inv_return
        self.cum_investment += inv_return

    # create DAY LOOP
    def one_day_passes(self):
        # create list of events that happen today and shuffle them to be random
        events_today = []
        events_today.extend(['entry'] * self.base_daily_entries[self.current_day])
        events_today.extend(['exit'] * self.base_daily_exits[self.current_day])
        events_today.extend(['wnxm_shift'])
        events_today.extend(['premium_income'])
        events_today.extend(['claim_outgo'])
        events_today.extend(['cover_amount_change'])
        events_today.extend(['delayed_exits'])
        events_today.extend(['investment_return'])
        shuffle(events_today)

        # CLOSE WNXM TO BOOK GAP, IF RELEVANT #
        while self.wnxm_price < self.book_value() * (1-model_params.wnxm_discount_to_book)\
            and model_params.gap_eth_sale < self.cap_pool:
            # set assumed individual arbitrage sale size
            eth_size = self.eth_sale_size(model_params.gap_eth_sale)
            # add exit to exit queue
            self.single_exit(eth=eth_size)
            # move wNXM price (based on depth at t=0)
            self.wnxm_price *= (1 + model_params.wnxm_arb_change)

        # LOOP THROUGH EVENTS OF DAY
        for event in events_today:
            #-----SINGLE ENTRIES-----#
            if event == 'entry':
                # no entries if wnxm price is below book,
                # instead move wnxm price up by 0.1%
                if self.wnxm_price < self.book_value():
                    self.wnxm_price *= (1 + model_params.wnxm_entry_change)
                # draw entry size from lognormal distribution
                # scaled to active cover amount (mainly to avoid buys when no cover)
                else:
                    eth_size = lognorm.rvs(s=model_params.entry_shape,
                                       loc=model_params.entry_loc,
                                       scale=model_params.entry_scale)\
                                        * self.act_cover_scaler()

                    self.single_entry(eth=eth_size)

            #-----SINGLE EXITS-----#
            elif event == 'exit':
                # no exits if wnxm price is above book
                # instead move wnxm price down
                if self.wnxm_price > self.book_value():
                    self.wnxm_price *= (1 - model_params.wnxm_exit_change)
                elif self.exit_queue_size(denom='eth') >= self.cap_pool \
                    or self.exit_queue_size(denom='nxm') >= self.nxm_supply:
                    continue
                # draw exit size from lognormal distribution
                else:
                    eth_size = lognorm.rvs(s=model_params.exit_shape,
                                        loc=model_params.exit_loc,
                                        scale=model_params.exit_scale)
                    # make sure sale doesn't take mcrp below 1
                    eth_size = self.eth_sale_size(eth_size)

                    self.single_exit(eth=eth_size)

            #-----WNXM RANDOM MARKET MOVEMENT-----#
            elif event == 'wnxm_shift':
                self.wnxm_shift()

            #-----PREMIUM INCOME TO POOL-----#
            elif event == 'premium_income':
                self.premium_income()

            #-----DAILY CHANGE IN COVER AMOUNT-----#
            elif event == 'cover_amount_change':
                self.cover_amount_shift()

            #-----CLAIM EVENT-----#
            elif event == 'claim_outgo':
                self.claim_payout()

            #-----DELAYED EXITS-----#
            elif event == 'delayed_exits':
                if self.current_day == 0:
                    continue
                self.delayed_exits()

            #-----INVESTMENT RETURN-----#
            elif event == 'investment_return':
                self.investment_return()

        # append values to tracking metrics
        self.mcr_prediction.append(self.mcr())
        self.cap_pool_prediction.append(self.cap_pool)
        self.exit_queue_eth_prediction.append(self.exit_queue_size())
        self.exit_queue_nxm_prediction.append(self.exit_queue_size(denom='nxm'))
        self.dca_prediction.append(self.dca())
        self.book_value_prediction.append(self.book_value())
        self.mcrp_prediction.append(self.mcrp(self.dca()))
        self.wnxm_prediction.append(self.wnxm_price)
        self.nxm_supply_prediction.append(self.nxm_supply)
        self.premium_prediction.append(self.cum_premiums)
        self.claim_prediction.append(self.cum_claims)
        self.act_cover_prediction.append(self.act_cover)
        self.num_exits_prediction.append(self.exit_array.shape[0] - 1)
        self.investment_return_prediction.append(self.cum_investment)

        self.current_day += 1
