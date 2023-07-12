'''
Define the Buying and Selling RAMM pools as a class (protocol only)
This allows us to track the different variables as they change over time
in a consistent manner.
Buying and selling mechanisms are virtual Uni v2 pools with the following features:
 - Price decreases upon sells and increases upon buys from the system
 - Buy pool desabled below target and sell pool disabled above target
 - Ratchet mechanism operates to bring the price towards target from below and above for the two pools
 - Liquidity mechanism to bring the pool liquidity towards a target liquidity
 - Target changes over time as buys/sells occur

 Note that this version can't be run by itself as it doesn't specify Stochastic vs Determinstic attributes

 The daily_printout parameter can print out some the pre-arbitrage, pre-event and post-event information for a specific day
 If these printouts are desired, set the parameter to a specific day (defaults to 0)
'''

import numpy as np
from random import shuffle

from BondingCurveNexus import sys_params, model_params

class RAMMMarkets:

    def __init__(self, daily_printout_day=0):
        # OPENING STATE of system upon initializing a projection instance
        # start at day 0
        self.current_day = 0
        # set daily printout parameter. If not specified, it defaults to 0 and no printouts happen
        self.daily_printout_day = daily_printout_day
        # set current state of system
        self.act_cover = sys_params.act_cover_now
        self.cap_pool = sys_params.cap_pool_now
        self.nxm_supply = sys_params.nxm_supply_now
        self.wnxm_supply = sys_params.wnxm_supply_now
        self.wnxm_price = sys_params.wnxm_price_now

        # set ETH value for wNXM price shift as a result of 1 ETH of buy/sell
        self.wnxm_move_size = model_params.wnxm_move_size

        # OPENING STATE of RAMM pools

        # BELOW BOOK
        # set initial ETH liquidity as initial parameter
        self.sell_liquidity_eth = sys_params.open_liq_sell
        # set initial NXM liquidity based on opening wnxm price
        # in practice we can start much lower than wnxm price
        # but for simulation purposes this is the first interesting point
        self.sell_liquidity_nxm = self.sell_liquidity_eth / self.wnxm_price
        # set initial invariant
        self.sell_invariant = self.sell_liquidity_eth * self.sell_liquidity_nxm
        # set target liquidity for the below book pool in ETH
        self.sell_target_liq = sys_params.target_liq_sell

        # ABOVE BOOK
        # set initial ETH liquidity as initial parameter
        self.buy_liquidity_eth = sys_params.open_liq_buy
        # set initial NXM liquidity based on opening wnxm price
        # in practice we can start much lower than wnxm price
        # but for simulation purposes this is the first interesting point
        self.buy_liquidity_nxm = self.buy_liquidity_eth /\
                                (self.book_value() * (1 + sys_params.oracle_buffer))
        # set initial invariant
        self.buy_invariant = self.buy_liquidity_eth * self.buy_liquidity_nxm
        # set target liquidity for the below book pool in ETH
        self.buy_target_liq = sys_params.target_liq_buy

        # base entries and exits - set to zero here
        # set stochasically or deterministically in subclasses
        self.base_daily_platform_buys = np.zeros(shape=model_params.model_days, dtype=int)
        self.base_daily_platform_sales = np.zeros(shape=model_params.model_days, dtype=int)

        # initiate and set cumulative counters to zero
        self.eth_sold = 0
        self.eth_acquired = 0
        self.nxm_burned = 0
        self.nxm_minted = 0
        self.wnxm_removed = 0
        self.wnxm_created = 0

        # set tracking lists for individual instance
        self.cap_pool_prediction = [self.cap_pool]
        self.sell_nxm_price_prediction = [self.sell_nxm_price()]
        self.buy_nxm_price_prediction = [self.buy_nxm_price()]
        self.wnxm_price_prediction = [self.wnxm_price]
        self.nxm_supply_prediction = [self.nxm_supply]
        self.wnxm_supply_prediction = [self.wnxm_supply]
        self.book_value_prediction = [self.book_value()]
        self.sell_liquidity_nxm_prediction = [self.sell_liquidity_nxm]
        self.sell_liquidity_eth_prediction = [self.sell_liquidity_eth]
        self.buy_liquidity_nxm_prediction = [self.buy_liquidity_nxm]
        self.buy_liquidity_eth_prediction = [self.buy_liquidity_eth]
        self.eth_sold_prediction = [self.eth_sold]
        self.eth_acquired_prediction = [self.eth_acquired]
        self.nxm_burned_prediction = [self.nxm_burned]
        self.nxm_minted_prediction = [self.nxm_minted]
        self.wnxm_removed_prediction = [self.wnxm_removed]
        self.wnxm_created_prediction = [self.wnxm_created]

    # INSTANCE FUNCTIONS
    # to calculate a variety of ongoing metrics & parameters
    # and update the system accordingly

    # calculate book value from current assets & nxm supply.
    def book_value(self):
        if self.nxm_supply == 0:
            return 0
        return self.cap_pool/self.nxm_supply

    # calculate nxm price for sells in ETH from virtual RAMM pool
    def sell_nxm_price(self):
        return self.sell_liquidity_eth / self.sell_liquidity_nxm

    # calculate nxm price for buys in ETH from virtual RAMM pool
    def buy_nxm_price(self):
        return self.buy_liquidity_eth / self.buy_liquidity_nxm

    # function to determine the random sizing of a buy/sell interaction
    # either with platform or wNXM market
    def nxm_sale_size(self):
        # defined in stoch v det subclasses - can be stochastic or deterministic
        return 0

    def nxm_buy_size(self):
        # defined in stoch v det subclasses - can be stochastic or deterministic
        return 0

    # one platform sale of n_nxm NXM
    def platform_nxm_sale(self, n_nxm):

        # limit number to total NXM
        n_nxm = min(n_nxm, self.nxm_supply)

        # add sold NXM to pool
        self.sell_liquidity_nxm += n_nxm
        self.nxm_supply -= n_nxm

        # establish new value of eth in pool
        new_eth = self.sell_invariant / self.sell_liquidity_nxm
        delta_eth = self.sell_liquidity_eth - new_eth

        # add ETH removed and nxm burned to cumulative total, update capital pool
        self.eth_sold += delta_eth
        self.cap_pool -= delta_eth
        self.nxm_burned += n_nxm

        # update ETH liquidity & invariant
        self.sell_liquidity_eth = new_eth
        self.sell_invariant = self.sell_liquidity_eth * self.sell_liquidity_nxm

    # one platform buy of n_nxm NXM
    def platform_nxm_buy(self, n_nxm):

        # assume noone buys NXM above a multiple of book
        if self.buy_nxm_price() > self.book_value() * model_params.nxm_book_value_multiple:
            pass

        else:
            # limit number of single buy to 50% of NXM liquidity to avoid silly results
            n_nxm = min(n_nxm, 0.5 * self.buy_liquidity_nxm)

            # remove bought NXM from pool and add actual mint to supply
            self.buy_liquidity_nxm -= n_nxm
            self.nxm_supply += n_nxm

            # establish new value of eth in pool
            new_eth = self.buy_invariant / self.buy_liquidity_nxm
            delta_eth = new_eth - self.buy_liquidity_eth

            # add ETH acquired and nxm minted to cumulative total, update capital pool
            self.eth_acquired += delta_eth
            self.cap_pool += delta_eth
            self.nxm_minted += n_nxm

            # update ETH liquidity & invariant
            self.buy_liquidity_eth = new_eth

    # WNXM MARKET FUNCTIONS
    def wnxm_market_buy(self, n_wnxm, remove=True):
        # limit number of wnxm bought to total supply
        n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole buy happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # increase price depending on defined liquidity parameters
        self.wnxm_price += n_eth * self.wnxm_move_size

        # if used for arb, remove from supply
        if remove:
            self.wnxm_supply -= n_wnxm
            self.wnxm_removed += n_wnxm

    def wnxm_market_sell(self, n_wnxm, create=True):
        # limit number of wnxm sold to total supply unless new wnxm is created
        if not create:
            n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole sell happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # decrease price depending on defined liquidity parameters
        self.wnxm_price -= n_eth * self.wnxm_move_size

        # if used for arb, add to supply (& limit by nxm supply)
        if create:
            old_supply = self.wnxm_supply
            self.wnxm_supply = min(self.wnxm_supply + n_wnxm, self.nxm_supply)
            self.wnxm_created += self.wnxm_supply - old_supply

 # daily percentage change in wNXM price
 # represents buys/sells in wnxm market without interacting with platform
    def wnxm_shift(self):
        self.wnxm_price *= 1

    # WNXM-NXM ARBITRAGE TRANSACTION FUNCTIONS
    def arb_sale_transaction(self):
        # establish size of nxm sell, limit to number of nxm supply and wnxm supply
        num = min(self.nxm_sale_size(), self.wnxm_supply, self.nxm_supply)
        # buy from open market
        self.wnxm_market_buy(n_wnxm=num, remove=True)
        # sell to platform
        self.platform_nxm_sale(n_nxm=num)

    def arb_buy_transaction(self):
        # establish size of nxm buy, limit to 50% of nxm liquidity in virtual pool to avoid spikes
        num = min(self.nxm_buy_size(), self.buy_liquidity_nxm * 0.5)
        # buy from platform
        self.platform_nxm_buy(n_nxm=num)
        # sell to open market
        self.wnxm_market_sell(n_wnxm=num, create=True)

    def arbitrage(self):
        # system price > wnxm_price arb
            # platform sale price has to be higher than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while  self.sell_nxm_price() > self.wnxm_price and \
                self.nxm_supply > 0 and self.wnxm_supply > 0:
            self.arb_sale_transaction()

        # system price < wnxm_price arb
            # buys disabled below book
            # platform price has to be lower than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while self.buy_nxm_price() < self.wnxm_price and \
                self.nxm_supply > 0:
            self.arb_buy_transaction()

    # RATCHET & LIQUIDITY FUNCTIONS
    def buy_ratchet(self):
        '''
        Function used to ratchet price downwards and remove liquidity for the above BV/buy pool.
        '''
        # establish price movement required to be relevant percentage of BV
        price_movement = self.book_value() * sys_params.ratchet_down_perc / model_params.ratchets_per_day

        # establish target price and cap at book value + oracle buffer
        target_price = max(self.buy_nxm_price() - price_movement,
                           self.book_value() * (1 + sys_params.oracle_buffer))

        # find new liquidity by moving down to target at daily percentage rate
        # divided by number of times we're ratcheting per day
        # limit at target
        if self.buy_liquidity_eth > self.buy_target_liq:
            self.buy_liquidity_eth = max(self.buy_liquidity_eth - self.buy_target_liq * sys_params.liq_out_perc / model_params.ratchets_per_day,
                                    self.buy_target_liq)

        # update NXM liquidity to reflect new price & new liquidity
        self.buy_liquidity_nxm = self.buy_liquidity_eth / target_price

        # update invariant
        self.buy_invariant = self.buy_liquidity_eth * self.buy_liquidity_nxm


    def sell_ratchet(self):
        '''
        Function used to ratchet price upwards and add liquidity for the below BV/sell pool.
        '''
        # establish price movement required to be relevant percentage of BV
        price_movement = self.book_value() * sys_params.ratchet_up_perc / model_params.ratchets_per_day

        # establish target price and cap at book value - oracle buffer
        target_price = max(self.sell_nxm_price(), min(self.sell_nxm_price() + price_movement,
                           self.book_value() * (1 - sys_params.oracle_buffer)))

        # find new liquidity by moving up to target at daily percentage rate
        # divided by number of times we're moving liquidity per day
        # limit at target
        if self.sell_liquidity_eth < self.sell_target_liq:
            self.sell_liquidity_eth = min(self.sell_liquidity_eth + self.sell_target_liq * sys_params.liq_in_perc / model_params.ratchets_per_day,
                                    self.sell_target_liq)

        # update NXM liquidity to reflect new price
        self.sell_liquidity_nxm = self.sell_liquidity_eth / target_price

        # update invariant
        self.sell_invariant = self.sell_liquidity_eth * self.sell_liquidity_nxm

    # create DAY LOOP
    def one_day_passes(self):
        # create list of events and shuffle it
        events_today = []
        events_today.extend(['ratchet'] * model_params.ratchets_per_day)
        events_today.extend(['wnxm_shift'] * model_params.wnxm_shifts_per_day)
        events_today.extend(['platform_buy'] * self.base_daily_platform_buys[self.current_day])
        events_today.extend(['platform_sale'] * self.base_daily_platform_sales[self.current_day])
        shuffle(events_today)

        # LOOP THROUGH EVENTS OF DAY
        for event in events_today:

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print pre-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - pre-arbitrage:
                        sell_nxm_price = {self.sell_nxm_price()}, buy_nxm_price = {self.buy_nxm_price()}
                        book_value = {self.book_value()},
                        cap_pool = {self.cap_pool}, nxm_supply = {self.nxm_supply}
                ''')

            #-----WNXM ARBITRAGE-----#
            # happens in between all events
            self.arbitrage()

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print post-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - post-arbitrage:
                        sell_nxm_price = {self.sell_nxm_price()}, buy_nxm_price = {self.buy_nxm_price()}
                        book_value = {self.book_value()},
                        cap_pool = {self.cap_pool}, nxm_supply = {self.nxm_supply}
                ''')

            #-----RATCHET-----#
            if event == 'ratchet':
                # up for below BV/sell pool
                self.sell_ratchet()
                # down for above BV/buy pool
                self.buy_ratchet()

            #-----WNXM SHIFT-----#
            if event == 'wnxm_shift':
                self.wnxm_shift()

            #-----PLATFORM BUY-----#
            # not arbitrage-driven
            if event == 'platform_buy':
                # with wNXM in place, don't do buys if buy price is above wNXM price
                # assume someone would buy wNXM on open market instead
                # need wnxm supply to exist
                if round(self.buy_nxm_price(), 8) > round(self.wnxm_price, 8) and \
                    self.wnxm_supply > 0:
                    self.wnxm_market_buy(n_wnxm=self.nxm_buy_size(), remove=False)
                else:
                    self.platform_nxm_buy(n_nxm=self.nxm_buy_size())

            #-----PLATFORM SALE-----#
            # not arbitrage-driven
            if event == 'platform_sale':
                # with wNXM in place, don't do sells if wNXM price is above platform
                # assume someone would sell wNXM on open market instead
                if round(self.sell_nxm_price(), 8) < round(self.wnxm_price, 8):
                    self.wnxm_market_sell(n_wnxm=self.nxm_sale_size(), create=False)
                else:
                    self.platform_nxm_sale(n_nxm=self.nxm_sale_size())

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print post-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - post-event:
                        sell_nxm_price = {self.sell_nxm_price()}, buy_nxm_price = {self.buy_nxm_price()}
                        book_value = {self.book_value()},
                        cap_pool = {self.cap_pool}, nxm_supply = {self.nxm_supply}
                ''')

        # append values to tracking metrics
        self.cap_pool_prediction.append(self.cap_pool)
        self.sell_nxm_price_prediction.append(self.sell_nxm_price())
        self.buy_nxm_price_prediction.append(self.buy_nxm_price())
        self.wnxm_price_prediction.append(self.wnxm_price)
        self.nxm_supply_prediction.append(self.nxm_supply)
        self.wnxm_supply_prediction.append(self.wnxm_supply)
        self.book_value_prediction.append(self.book_value())
        self.sell_liquidity_nxm_prediction.append(self.sell_liquidity_nxm)
        self.sell_liquidity_eth_prediction.append(self.sell_liquidity_eth)
        self.buy_liquidity_nxm_prediction.append(self.buy_liquidity_nxm)
        self.buy_liquidity_eth_prediction.append(self.buy_liquidity_eth)
        self.eth_sold_prediction.append(self.eth_sold)
        self.eth_acquired_prediction.append(self.eth_acquired)
        self.nxm_burned_prediction.append(self.nxm_burned)
        self.nxm_minted_prediction.append(self.nxm_minted)
        self.wnxm_removed_prediction.append(self.wnxm_removed)
        self.wnxm_created_prediction.append(self.wnxm_created)

        # increment day
        self.current_day += 1