'''
Define the Buying and Selling Mechanism as a class, in addition to wNXM market movements and arbitrage
This allows us to track the different variables as they change over time
in a consistent manner.
Buying and selling mechanism is a virtual Uni v2 pool with the following features:
 - Price decreases upon sells and increases upon buys from the system
 - Buys desabled below book value and sells disabled above book value
 - Ratchet mechanism operates to bring the price towards book value from below and above
 - Liquidity mechanism to bring the pool liquidity towards a target liquidity

 Note that this version can't be run by itself as it doesn't specify Stochastic vs Determinstic attributes

 The daily_printout parameter can print out some the pre-arbitrage, pre-event and post-event information for a specific day
 If these printouts are desired, set the parameter to a specific day (defaults to 0)
'''

import numpy as np
from random import shuffle, choice

from BondingCurveNexus import sys_params, model_params

class UniPoolMarkets:

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

        # OPENING STATE of virtual uni pool
        # set initial ETH liquidity as initial parameter
        self.liquidity_eth = sys_params.open_liq_sell
        # set initial NXM liquidity based on opening wnxm price
        # in practice we can start much lower than wnxm price
        # but for simulation purposes this is the first interesting point
        self.liquidity_nxm = self.liquidity_eth / self.wnxm_price
        # set initial invariant
        self.invariant = self.liquidity_eth * self.liquidity_nxm

        # set target liquidity for the virtual pool in ETH
        self.target_liq = sys_params.target_liq_sell

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
        self.nxm_price_prediction = [self.nxm_price()]
        self.wnxm_price_prediction = [self.wnxm_price]
        self.nxm_supply_prediction = [self.nxm_supply]
        self.wnxm_supply_prediction = [self.wnxm_supply]
        self.book_value_prediction = [self.book_value()]
        self.liquidity_nxm_prediction = [self.liquidity_nxm]
        self.liquidity_eth_prediction = [self.liquidity_eth]
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

    # calculate system nxm price in ETH from virtual Uni v2-style pool
    def nxm_price(self):
        return self.liquidity_eth / self.liquidity_nxm

    # function to determine the random sizing of a buy/sell interaction
    # either with platform or wNXM market
    def nxm_sale_size(self):
        # defined in stoch v det subclasses - can be stochastic or deterministic
        return 0

    # one platform sale of n_nxm NXM
    def platform_nxm_sale(self, n_nxm):

        # sells disabled above book, so above book user would sell wNXM on open market instead
        if round(self.nxm_price(), 8) > round(self.book_value(), 8):
            self.wnxm_market_sell(n_wnxm=n_nxm, create=False)

        else:
            # limit number to total NXM
            n_nxm = min(n_nxm, self.nxm_supply)

            # add sold NXM to pool
            self.liquidity_nxm += n_nxm
            self.nxm_supply -= n_nxm

            # establish new value of eth in pool
            new_eth = self.invariant / self.liquidity_nxm
            delta_eth = self.liquidity_eth - new_eth

            # add ETH removed and nxm burned to cumulative total, update capital pool
            self.eth_sold += delta_eth
            self.cap_pool -= delta_eth
            self.nxm_burned += n_nxm

            # update ETH liquidity & invariant
            self.liquidity_eth = new_eth
            self.invariant = self.liquidity_eth * self.liquidity_nxm

    # one platform buy of n_nxm NXM
    def platform_nxm_buy(self, n_nxm):

        # buys disabled below book, so user would buy wNXM on open market instead
        if round(self.nxm_price(), 4) < round(self.book_value(), 4):
            self.wnxm_market_buy(n_wnxm=n_nxm, remove=False)

        # assume noone buys NXM above a multiple of book
        elif self.nxm_price() > self.book_value() * model_params.nxm_book_value_multiple:
            pass

        else:
            # limit number of single buy to 50% of NXM liquidity to avoid silly results
            n_nxm = min(n_nxm, 0.5 * self.liquidity_nxm)

            # remove bought NXM from pool and add actual mint to supply
            self.liquidity_nxm -= n_nxm
            self.nxm_supply += n_nxm

            # establish new value of eth in pool
            new_eth = self.invariant / self.liquidity_nxm
            delta_eth = new_eth - self.liquidity_eth

            # add ETH acquired and nxm minted to cumulative total, update capital pool
            self.eth_acquired += delta_eth
            self.cap_pool += delta_eth
            self.nxm_minted += n_nxm

            # update ETH liquidity
            self.liquidity_eth = new_eth

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
        num = min(self.nxm_sale_size(), self.liquidity_nxm * 0.5)
        # buy from platform
        self.platform_nxm_buy(n_nxm=num)
        # sell to open market
        self.wnxm_market_sell(n_wnxm=num, create=True)

    def arbitrage(self):
        # system price > wnxm_price arb
            # disable sales below book
            # platform sale price has to be higher than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while  self.nxm_price() <= self.book_value() and \
        self.nxm_price() > self.wnxm_price and \
        self.nxm_supply > 0 and self.wnxm_supply > 0:
            self.arb_sale_transaction()

        # system price < wnxm_price arb
            # buys disabled below book
            # platform price has to be lower than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while self.nxm_price() >= self.book_value() and \
        self.nxm_price() < self.wnxm_price and \
        self.nxm_supply > 0:
            self.arb_buy_transaction()

    # RATCHET FUNCTIONS
    def ratchet_down(self):
        # establish price movement required to be relevant percentage of BV
        price_movement = self.book_value() * sys_params.ratchet_down_perc / model_params.ratchets_per_day

        # establish target price and cap at book value
        target_price = max(self.nxm_price() - price_movement, self.book_value())

        # update NXM liquidity to reflect new price
        self.liquidity_nxm = self.liquidity_eth / target_price

        # update invariant
        self.invariant = self.liquidity_eth * self.liquidity_nxm

    def ratchet_up(self):
        # establish price movement required to be relevant percentage of BV
        price_movement = self.book_value() * sys_params.ratchet_up_perc / model_params.ratchets_per_day

        # establish target price and cap at book value
        target_price = min(self.nxm_price() + price_movement, self.book_value())

        # update NXM liquidity to reflect new price
        self.liquidity_nxm = self.liquidity_eth / target_price

        # update invariant
        self.invariant = self.liquidity_eth * self.liquidity_nxm

    # LIQUIDITY FUNCTIONS
    def liq_move(self, new_liq):
        # solve for required NXM liquidity first from current NXM price
        self.liquidity_nxm = new_liq / self.nxm_price()

        # update ETH liquidity
        self.liquidity_eth = new_liq

        # update invariant
        self.invariant = self.liquidity_nxm * self.liquidity_eth

    def new_liq(self, kind):
        # move ETH liquidity towards target

        # downward move
        if kind == 'down':
            # don't move if below book
            if self.nxm_price() < self.book_value():
                return self.liquidity_eth

        # if above book & above target liq, down to target at daily percentage rate (limit at target)
        # divided by number of times we're moving liquidity per day
            return max(self.liquidity_eth - self.target_liq * sys_params.liq_out_perc / model_params.ratchets_per_day,
                       self.target_liq)

        # if below target liq, up to target at daily percentage rate (limit at target)
        # divided by number of times we're moving liquidity per day
        if kind == 'up':
            return min(self.liquidity_eth + self.target_liq * sys_params.liq_in_perc / model_params.ratchets_per_day,
                       self.target_liq)

    # create DAY LOOP
    def one_day_passes(self):
        # create list of events and shuffle it
        events_today = []
        events_today.extend(['ratchet'] * model_params.ratchets_per_day)
        events_today.extend(['liq_move'] * model_params.ratchets_per_day)
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
                        nxm_price = {self.nxm_price()}, wnxm_price = {self.wnxm_price}
                        book_value = {self.book_value()}, cap_pool = {self.cap_pool},
                        nxm_supply = {self.nxm_supply}, wnxm_supply = {self.wnxm_supply}
                        liquidity_nxm = {self.liquidity_nxm}, liquidity_eth = {self.liquidity_eth}
                ''')

            #-----WNXM ARBITRAGE-----#
            # happens in between all events
            self.arbitrage()

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print post-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - post-arbitrage:
                        nxm_price = {self.nxm_price()}, wnxm_price = {self.wnxm_price}
                        book_value = {self.book_value()}, cap_pool = {self.cap_pool},
                        nxm_supply = {self.nxm_supply}, wnxm_supply = {self.wnxm_supply}
                        liquidity_nxm = {self.liquidity_nxm},liquidity_eth = {self.liquidity_eth}
                ''')

            #-----RATCHET-----#
            if event == 'ratchet':
                # up if below BV
                if self.book_value() > self.nxm_price():
                    self.ratchet_up()
                # down if above BV (but ratchet_down method only enabled in one-sided subclass)
                if self.book_value() < self.nxm_price():
                    self.ratchet_down()

            #-----LIQUIDITY MOVE-----#
            if event == 'liq_move':
                # liquidity down towards target if liquidity above target
                if self.liquidity_eth > self.target_liq:
                    self.liq_move(new_liq=self.new_liq(kind='down'))

                # liquidity up towards target if liquidity below target
                if self.liquidity_eth < self.target_liq:
                    self.liq_move(new_liq=self.new_liq(kind='up'))

            #-----WNXM SHIFT-----#
            if event == 'wnxm_shift':
                self.wnxm_shift()

            #-----PLATFORM BUY-----#
            # not arbitrage-driven
            if event == 'platform_buy':
                # doesn't happen if wnxm price is below platform price
                # instead a buy happens of wNXM on open market, assuming there are wnxm to buy
                if self.nxm_price() > self.wnxm_price and self.wnxm_supply > 0:
                    self.wnxm_market_buy(n_wnxm=self.nxm_sale_size(), remove=False)

                # otherwise execute the buy (subject to constraints within instance method)
                else:
                    self.platform_nxm_buy(n_nxm=self.nxm_sale_size())

            #-----PLATFORM SALE-----#
            # not arbitrage-driven
            if event == 'platform_sale':
                # doesn't happen if wnxm price is above platform price
                # instead a sell happens of wNXM on open market
                if self.nxm_price() < self.wnxm_price:
                    self.wnxm_market_sell(n_wnxm=self.nxm_sale_size(), create=False)

                # otherwise execute the sell (subject to constraints within instance method)
                else:
                    self.platform_nxm_sale(n_nxm=self.nxm_sale_size())

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print post-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - post-event:
                        nxm_price = {self.nxm_price()}, wnxm_price = {self.wnxm_price}
                        book_value = {self.book_value()}, cap_pool = {self.cap_pool},
                        nxm_supply = {self.nxm_supply}, wnxm_supply = {self.wnxm_supply}
                        liquidity_nxm = {self.liquidity_nxm},liquidity_eth = {self.liquidity_eth}
                ''')

        # append values to tracking metrics
        self.cap_pool_prediction.append(self.cap_pool)
        self.nxm_price_prediction.append(self.nxm_price())
        self.wnxm_price_prediction.append(self.wnxm_price)
        self.nxm_supply_prediction.append(self.nxm_supply)
        self.wnxm_supply_prediction.append(self.wnxm_supply)
        self.book_value_prediction.append(self.book_value())
        self.liquidity_nxm_prediction.append(self.liquidity_nxm)
        self.liquidity_eth_prediction.append(self.liquidity_eth)
        self.eth_sold_prediction.append(self.eth_sold)
        self.eth_acquired_prediction.append(self.eth_acquired)
        self.nxm_burned_prediction.append(self.nxm_burned)
        self.nxm_minted_prediction.append(self.nxm_minted)
        self.wnxm_removed_prediction.append(self.wnxm_removed)
        self.wnxm_created_prediction.append(self.wnxm_created)

        # increment day
        self.current_day += 1
