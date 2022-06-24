'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
in a consistent manner.
'''
from scipy.stats import lognorm
import numpy as np
from random import shuffle

from BondingCurveNexus import sys_params
from BondingCurveNexus import model_params

class NexusSystem:

    def __init__(self):
        # OPENING STATE of system upon initializing a projection instance
        self.current_day = 0
        self.act_cover = sys_params.act_cover_now
        self.nxm_supply = sys_params.nxm_supply_now
        self.cap_pool = sys_params.cap_pool_now
        self.exit_array = np.zeros((1, 1 + model_params.model_days +
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
    def mcr(self):
        return self.act_cover / sys_params.capital_factor

    # calculate mcr% from current assets and mcr size.
    # Specify whether to use all current assets or remove exit queue
    def mcrp(self, capital):
        return capital/self.mcr()

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

    # Bond bonus calculation, based on MCR% after allowing for exit queue
    # Function with upper limit on exponent, parameterised
    def bond_bonus(self):
        return sys_params.entry_bond_max_interest * (1 - np.exp(
                                                    -sys_params.entry_bond_shape *
                                                    self.mcrp(self.dca())
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

    # create numpy row vector of nxm received with bonus at appropriate time
    # and append it to entry array
    # update parameters of system
    def single_entry(self, eth):
        # work out number of nxm user could receive instantly (floor of book value)
        nxm_obtained = eth / max(self.book_value(), self.wnxm_price)

        # if MCR% < 1, encourage entries through bond interest
        if self.mcrp(self.dca()) < 1:
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

    # create numpy row vector reflecting the possibilities of exit
    # including 0 for first 14 days
    # instant 100% after 14 days if mcrp > 1 and moving up curve to 100% if not
    def single_exit(self, eth):
        # set up single empty row vector of maximum possible length
        # + 1 (for storing nxm value)
        row_vec = np.zeros(model_params.model_days + sys_params.base_exit_days +
                           sys_params.mcrp_max_days + sys_params.queue_max_days +
                           sys_params.option_exit_period + 1)

        # determine the first day user can exit from today
        start_day = self.current_day + sys_params.minimum_exit_period
        # if mcr% > 100%, user has option to exit after minimum waiting period
        # at full book value for 30 days
        if self.mcrp(self.dca()) > 1:
            ratio_array = np.ones(sys_params.option_exit_period)
            # replace relevant days with ones in array
            row_vec[start_day:start_day + sys_params.option_exit_period] = ratio_array

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

        # place full nxm value in final position on row vector
        row_vec[-1] = nxm

        # append vector to exit array
        self.exit_array = np.vstack((self.exit_array, row_vec))

    # eth sizer - throttle size of sale if it takes mcrp below 1
    def eth_sale_size(self, eth):
        # if mcr% > 100%,
        # check whether size reduces mcrp below 1 & turn eth_size into maximum possible
        # such that mcrp doesn't go below 1
        if self.mcrp(self.dca()) > 1:
            if self.mcrp(dca() - gap_eth_sale) <= 1:
                    eth_size = dca() - mcr()

    # simulate exits from exit queue in a single day
    def delayed_exits(self):
        # create empty list of rows to remove at end of day
        removal_rows = []
        # slice exit array to today only
        today_column = self.exit_array[:, self.current_day]
        # loop through today's ratio values (& indices) and check if there is an exit
        for idx, ratio in np.ndenumerate(today_column):
            # if ratio value is zero, exit is not possible,
            # so only roll dice for non-zero values
            if ratio != 0:
                # if below statement is true, this implies an exit
                if np.random.random() < ratio**model_params.p_exit_exponent *\
                                        model_params.p_exit_full:
                    # burn nxm value of row
                    self.nxm_supply -= self.exit_array[idx[0], -1]
                    # remove eth value from capital pool
                    self.cap_pool -= self.exit_array[idx[0], -1] * ratio * self.book_value()
                    # add row to removal rows
                    removal_rows.append(idx[0])

            # check whether the option hasn't been exercised
            # this means it failed the previous if statment (so ratio is zero)
            # and the ratio the day before today should be 1
            # burn 10% of nxm and add to rows to be removed from exit array
            elif self.exit_array[idx[0], self.current_day-1] == 1:
                self.nxm_supply -= sys_params.option_cost *\
                                    self.exit_array[idx[0], -1]
                removal_rows.append(idx[0])

        # remove expired and successful exit rows from exit array
        self.exit_array = np.delete(self.exit_array, removal_rows, axis=0)

    # daily percentage change in wNXM price
    def wnxm_shift(self):
        self.wnxm_price *= (1 + self.base_daily_wnxm_change[self.current_day])

    # daily percentage change in active cover amount
    def cover_amount_shift(self):
        self.act_cover *= (1 + self.base_daily_cover_change[self.current_day])

    # premium & claim scaling based on active cover vs opening active cover
    def prem_claim_scaler(self):
        return self.act_cover / sys_params.act_cover_now

    # daily premium income and additions to nxm supply & cap pool
    # logged in cumulative premiums
    def premium_income(self):
        daily_premium = self.base_daily_premiums[self.current_day] * self.prem_claim_scaler()
        self.cap_pool += daily_premium
        self.nxm_supply += 0.5 * daily_premium/self.wnxm_price
        self.cum_premiums += daily_premium

    # claim payout - checks whether there are claims and if there is
    # size is randomised using a lognormal distribution
    # claim amount is removed from pool and 50% of corresponding staking nxm burnt
    # logged in cumulative claims
    def claim_payout(self):
        if self.claim_rolls[self.current_day] < model_params.claim_prob:
            claim_size = lognorm.rvs(s=model_params.claim_shape,
                                     loc=model_params.claim_loc,
                                     scale=model_params.claim_scale)
            self.nxm_supply -= 0.5 * claim_size/self.wnxm_price
            self.cap_pool -= claim_size
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
        events_today.extend(['claim_check'])
        events_today.extend(['cover_amount_change'])
        events_today.extend(['delayed_exits'])
        events_today.extend(['investment_return'])
        shuffle(events_today)

        # CLOSE WNXM TO BOOK GAP, IF RELEVANT #
        while self.wnxm_price < self.book_value()*\
                                (1-model_params.wnxm_discount_to_book):
            # set assumed individual arbitrage sale size
            eth_size = gap_eth_sale



#                     # reduce nxm supply and remove ETH from capital pool
#                     nxm_supply -= eth_size/wnxm_price  # book_value(dca())
#                     cap_pool -= eth_size

            # add row of potential NXM exits to exit array
            exit_array = np.vstack((exit_array, single_exit(eth=eth_size)))
#                     # burn 10% of NXM size
#                     nxm_supply -= gap_eth_sale/book_value(dca()) * option_cost

            # move wNXM price
            wnxm_price *= 1 + gap_wnxm_move(eth_size)

        # loop through day's events
        for event in events_today:
            #-----SINGLE ENTRIES-----#
            if event == 'entry':
                # no entries if wnxm price is below book
                if self.wnxm_price < self.book_value():
                    continue
                # draw entry size from lognormal distribution
                eth_size = lognorm.rvs(s=model_params.sale_shape,
                                       loc=model_params.sale_loc,
                                       scale=model_params.sale_scale)
                self.single_entry(eth=eth_size)

            #-----SINGLE EXITS & GAP CLOSING-----#
            elif event == 'exit':
                # no exits if wnxm price is above book
                if self.wnxm_price > self.book_value():
                    continue




                # SINGLE EXIT #
                # draw exit size from lognormal distribution
                eth_size = lognorm.rvs(s=sale_shape, loc=sale_loc, scale=sale_scale)

                    # if mcr% > 100%,
                    # check whether size reduces mcrp below 1 & turn eth_size into maximum possible
                    # such that mcrp doesn't go below 1
                if mcrp(dca()) > 1:
                    if mcrp(dca() - gap_eth_sale) <= 1:
                        eth_size = dca() - mcr()

        #             # reduce nxm supply and remove ETH from capital pool
        #             nxm_supply -= eth_size/wnxm_price # book_value(dca())
        #             cap_pool -= eth_size

        #             # add to exit queue if mcrp <= 1
        #             else:

                # add single exit to the exit array
                exit_array = np.vstack((exit_array, single_exit(eth=eth_size)))

        #                 # burn 10% of NXM size
        #                 nxm_supply -= eth_size/wnxm_price * option_cost # book_value(dca())

            #-----WNXM RANDOM MARKET MOVEMENT-----#
            elif event == 'wnxm_shift':
                # percentage change according to pre-defined normal distribution
                wnxm_price *= 1 + norm.rvs(loc=wnxm_drift, scale=wnxm_diffusion)

            #-----PREMIUM INCOME TO POOL-----#
            elif event == 'premium_income':
                # work out daily premium size in ETH assuming a lognormal distribution
                daily_premiums = lognorm.rvs(s=premium_shape, loc=premium_loc, scale=premium_scale) * prem_claim_scaler
                # 50% of premium size gets transformed to NXM and paid out to stakers
                # entry is at wNXM price
                cap_pool += daily_premiums
                nxm_supply += 0.5 * daily_premiums/wnxm_price
                cum_premiums += daily_premiums

            #-----DAILY CHANGE IN COVER AMOUNT-----#
            elif event == 'cover_amount_change':
                # random fluctuation based on normal distribution
                act_cover *= 1 + norm.rvs(loc=cover_amount_mean, scale=cover_amount_stdev)

            #-----CLAIM EVENT-----#
            elif event == 'claim_check':
                # check if claims occur
                if np.random.random() > claim_prob:
                    continue
                # if a claim has occured, determine size
                claim_size = lognorm.rvs(s=claim_shape, loc=claim_loc, scale=claim_scale) * prem_claim_scaler
                # burn 50% of nxm at wnxm price and remove claims amount from capital pool
                nxm_supply -= 0.5 * claim_size/wnxm_price
                cap_pool -= claim_size
                cum_claims += claim_size
                # NB: could introduce wNXM shock if claim is over a certain size?

            #-----BOND ENTRIES-----#
            ### commented out because makes more sense to add NXM to supply immediately
        #         elif event == 'bond_entries':
        #             # sum up entries on current day and add to NXM supply
        #             nxm_supply += np.sum(entry_array[:, current_day])

            #-----DELAYED EXITS-----#
            elif event == 'delayed_exits':
                # don't do this for first days within minimum exit period
                if current_day < minimum_exit_period:
                    continue

                removal_rows = []
                # slice exit array to current day & loop through entries
                current_exits = exit_array[:, current_day]
                for idx, number_nxm in np.ndenumerate(current_exits):
                    # if value is non-zero, check whether user chooses to exit
                    if number_nxm != 0:
                        # successful exit
                        if np.random.random() < p_exit(idx, number_nxm):
                            # burn full NXM value of row
                            nxm_supply -= np.max(exit_array[idx[0]])
                            # remove eth value from capital pool
                            cap_pool -= number_nxm * book_value(cap_pool)
                            # add row to removal_rows
                            removal_rows.append(idx[0])

                    # check whether the option hasn't been exercised - row should be removed & option cost burnt
                    elif exit_array[idx, current_day-1] != 0:
                        nxm_supply -= option_cost*exit_array[idx[0], current_day-1]
                        # add row to removal rows
                        removal_rows.append(idx[0])


                # remove rows from exit array:
                exit_array = np.delete(exit_array, removal_rows, axis=0)

            #-----INVESTMENT RETURN-----#
            elif event == 'investment_return':
                # daily return on capital pool
                inv_return = daily_investment_return * cap_pool
                cap_pool += inv_return
                cum_investment += inv_return

        mcr_prediction.append(mcr())
        cap_pool_prediction.append(cap_pool)
        exit_queue_eth_prediction.append(exit_queue_size())
        exit_queue_nxm_prediction.append(exit_queue_size(denom='nxm'))
        dca_prediction.append(dca())
        book_value_prediction.append(book_value(cap_pool))
        mcrp_prediction.append(mcrp(dca()))
        wnxm_prediction.append(wnxm_price)
        nxm_supply_prediction.append(nxm_supply)
        premium_prediction.append(cum_premiums)
        claim_prediction.append(cum_claims)
        act_cover_prediction.append(act_cover)
        num_exits_prediction.append(exit_array.shape[0])
        investment_return_prediction.append(cum_investment)

        current_day += 1
