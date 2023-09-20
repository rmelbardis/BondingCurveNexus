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

class RAMMHighLowCapProtocol:

    def __init__(self, daily_printout_day=0):
        # OPENING STATE of system upon initializing a projection instance
        # start at day 0 & step 0
        self.current_day = 0
        self.steps = 0
        # set daily printout parameter. If not specified, it defaults to 0 and no printouts happen
        self.daily_printout_day = daily_printout_day
        # set current state of system
        self.act_cover = sys_params.act_cover_now
        self.cap_pool = sys_params.cap_pool_now
        self.nxm_supply = sys_params.nxm_supply_now

        # set opening prices
        self.sell_open_price = 0.01418
        self.buy_open_price = 0.03566

        # OPENING STATE of RAMM pools

        # set initial ETH liquidity
        self.liq = sys_params.open_liq_sell
        # set target liquidity for the pools in ETH
        self.target_liq = sys_params.target_liq_sell

        # BELOW BOOK
        # set initial NXM liquidity based on opening wnxm price
        # in practice we can start much lower than wnxm price
        # but for simulation purposes this is the first interesting point
        self.liq_NXM_b = self.liq / self.sell_open_price
        # set initial invariant
        self.k_b = self.liq * self.liq_NXM_b

        # ABOVE BOOK
        # set initial NXM liquidity based on opening price
        self.liq_NXM_a = self.liq / self.buy_open_price
        # set initial invariant
        self.k_a = self.liq * self.liq_NXM_a

        # base entries and exits - set to zero here
        # set stochasically or deterministically in subclasses
        self.base_daily_protocol_buys = np.zeros(shape=model_params.model_days, dtype=int)
        self.base_daily_protocol_sales = np.zeros(shape=model_params.model_days, dtype=int)

        # initiate and set cumulative counters to zero
        self.eth_sold = 0
        self.eth_acquired = 0
        self.nxm_burned = 0
        self.nxm_minted = 0

        # set tracking lists for individual instance
        self.cap_pool_prediction = [self.cap_pool]
        self.spot_price_b_prediction = [self.spot_price_b()]
        self.spot_price_a_prediction = [self.spot_price_a()]
        self.nxm_supply_prediction = [self.nxm_supply]
        self.book_value_prediction = [self.book_value()]
        self.liq_prediction = [self.liq]
        self.liq_NXM_b_prediction = [self.liq_NXM_b]
        self.liq_NXM_a_prediction = [self.liq_NXM_a]
        self.eth_sold_prediction = [self.eth_sold]
        self.eth_acquired_prediction = [self.eth_acquired]
        self.nxm_burned_prediction = [self.nxm_burned]
        self.nxm_minted_prediction = [self.nxm_minted]

    # INSTANCE FUNCTIONS
    # to calculate a variety of ongoing metrics & parameters
    # and update the system accordingly

    # calculate mcr from current cover amount
    # minimum of 0.01 ETH to avoid division by zero
    def mcr(self):
        return max(0.01, self.act_cover / sys_params.capital_factor)

    # calculate book value from current assets & nxm supply.
    def book_value(self):
        if self.nxm_supply == 0:
            return 0
        return self.cap_pool/self.nxm_supply

    # calculate nxm price for sells in ETH from virtual RAMM pool
    def spot_price_b(self):
        return self.liq / self.liq_NXM_b

    # calculate nxm price for buys in ETH from virtual RAMM pool
    def spot_price_a(self):
        return self.liq / self.liq_NXM_a

    # function to determine the random sizing of a buy/sell interaction
    # either with protocol or wNXM market
    def nxm_sale_size(self):
        # defined in stoch v det subclasses - can be stochastic or deterministic
        return 0

    def nxm_buy_size(self):
        # defined in stoch v det subclasses - can be stochastic or deterministic
        return 0

    # calculate current ratios between high & low capitalization functionality
    def price_transition_ratio(self):
        return min(1, max(0,
                (self.cap_pool - self.mcr() - self.target_liq) / sys_params.price_transition_buffer))

    # calculate target for ratchet mechanism based on price transition ratio
    def ratchet_target(self):
        return min(self.book_value(),
                self.price_transition_ratio() * self.book_value() +
                (1 - self.price_transition_ratio()) * (self.spot_price_a() + self.spot_price_b()) / 2)

    # one protocol sale of n_nxm NXM
    def protocol_nxm_sale(self, n_nxm):

        # limit number to total NXM
        n_nxm = min(n_nxm, self.nxm_supply)

        # add sold NXM to pool
        self.liq_NXM_b += n_nxm
        self.nxm_supply -= n_nxm

        # establish new value of eth in pool
        new_eth = self.k_b / self.liq_NXM_b
        delta_eth = self.liq - new_eth

        # add ETH removed and nxm burned to cumulative total, update capital pool
        self.eth_sold += delta_eth
        self.cap_pool -= delta_eth
        self.nxm_burned += n_nxm

        # update above NXM reserve to maintain price after liquidity update
        self.liq_NXM_a = new_eth / self.spot_price_a()

        # update ETH liquidity & invariants
        self.liq = new_eth
        self.k_a = self.liq * self.liq_NXM_a
        self.k_b = self.liq * self.liq_NXM_b

    # one protocol buy of n_nxm NXM
    def protocol_nxm_buy(self, n_nxm):

        # assume noone buys NXM above a multiple of book
        if self.spot_price_a() > self.book_value() * model_params.nxm_book_value_multiple:
            pass

        else:
            # limit number of single buy to 50% of NXM liquidity to avoid silly results
            n_nxm = min(n_nxm, 0.5 * self.liq_NXM_a)

            # remove bought NXM from pool and add actual mint to supply
            self.liq_NXM_a -= n_nxm
            self.nxm_supply += n_nxm

            # establish new value of eth in pool
            new_eth = self.k_a / self.liq_NXM_a
            delta_eth = new_eth - self.liq

            # add ETH acquired and nxm minted to cumulative total, update capital pool
            self.eth_acquired += delta_eth
            self.cap_pool += delta_eth
            self.nxm_minted += n_nxm

            # update below NXM reserve to maintain price after liquidity update
            self.liq_NXM_b = new_eth / self.spot_price_b()

            # update ETH liquidity & invariants
            self.liq = new_eth
            self.k_a = self.liq * self.liq_NXM_a
            self.k_b = self.liq * self.liq_NXM_b

    # RATCHET & LIQUIDITY FUNCTIONS
    def buy_ratchet(self):
        '''
        Function used to ratchet price downwards and remove liquidity for the above BV/buy pool.
        '''
        # establish price movement required to be relevant percentage of target
        price_movement = self.ratchet_target() * sys_params.ratchet_down_perc / model_params.ratchets_per_day

        # establish target price and cap at target + oracle buffer
        target_price = max(self.spot_price_a() - price_movement,
                           self.ratchet_target() * (1 + sys_params.oracle_buffer))

        # if liquidity is above target and spot prices are above target
        # find new liquidity by moving down to target at daily percentage rate
        # divided by number of times we're ratcheting per day
        # limit at target
        if self.liq > self.target_liq:
            new_liq = max(self.liq - self.target_liq * sys_params.liq_out_perc / model_params.ratchets_per_day,
                                    self.target_liq)

        else:
            new_liq = self.liq

        # update NXM liquidity to reflect new price & new liquidity
        self.liq_NXM_a = new_liq / target_price

        # update NXM liquidity in below pool to keep price constant
        self.liq_NXM_b = new_liq / self.spot_price_b()

        # update liquidity and invariants
        self.liq = new_liq
        self.k_a = self.liq * self.liq_NXM_a
        self.k_b = self.liq * self.liq_NXM_b


    def sell_ratchet(self):
        '''
        Function used to ratchet price upwards and add liquidity for the below BV/sell pool.
        '''
        # establish price movement required to be relevant percentage of BV
        price_movement = self.ratchet_target() * sys_params.ratchet_up_perc / model_params.ratchets_per_day

        # establish target price and cap at book value - oracle buffer
        target_price = min(self.spot_price_b() + price_movement,
                           self.ratchet_target() * (1 - sys_params.oracle_buffer))

        # if liquidity is below target, spot prices are below target and we're still injecting
        # find new liquidity by moving up to target at daily percentage rate
        # divided by number of times we're moving liquidity per day
        # limit at target
        if self.liq < self.target_liq and self.cap_pool > self.mcr() + self.target_liq:
            new_liq = min(self.liq + self.target_liq * sys_params.liq_in_perc / model_params.ratchets_per_day,
                                    self.target_liq)

        else:
            new_liq = self.liq

        # update NXM liquidity to reflect new price
        self.liq_NXM_b = new_liq / target_price

        # update NXM liquidity in below pool to keep price constant
        self.liq_NXM_a = new_liq / self.spot_price_a()

        # update liquidity and invariants
        self.liq = new_liq
        self.k_a = self.liq * self.liq_NXM_a
        self.k_b = self.liq * self.liq_NXM_b

    # create DAY LOOP
    def one_day_passes(self):
        # create list of events and shuffle it
        events_today = []
        events_today.extend(['ratchet'] * model_params.ratchets_per_day)
        events_today.extend(['protocol_buy'] * self.base_daily_protocol_buys[self.current_day])
        events_today.extend(['protocol_sale'] * self.base_daily_protocol_sales[self.current_day])
        shuffle(events_today)

        # LOOP THROUGH EVENTS OF DAY
        for event in events_today:

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print pre-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - pre-event:
                        spot_price_b = {self.spot_price_b()}, spot_price_a = {self.spot_price_a()}
                        book_value = {self.book_value()}, cap_pool = {self.cap_pool}, nxm_supply = {self.nxm_supply}
                ''')

            #-----RATCHET-----#
            if event == 'ratchet':
                # up for below BV/sell pool
                self.sell_ratchet()
                # down for above BV/buy pool
                self.buy_ratchet()

            #-----protocol BUY-----#
            # not arbitrage-driven
            if event == 'protocol_buy':
                self.protocol_nxm_buy(n_nxm=self.nxm_buy_size())

            #-----protocol SALE-----#
            # not arbitrage-driven
            if event == 'protocol_sale':
                self.protocol_nxm_sale(n_nxm=self.nxm_sale_size())

           # optional daily printout
           # if daily_printout_day parameter is non-zero, print post-arbitrage params
            if self.daily_printout_day and self.current_day == self.daily_printout_day:
                print(f'''Day {self.daily_printout_day} - {event} - post-event:
                        spot_price_b = {self.spot_price_b()}, spot_price_a = {self.spot_price_a()}
                        book_value = {self.book_value()}, cap_pool = {self.cap_pool}, nxm_supply = {self.nxm_supply}
                ''')

        # append values to tracking metrics
        self.cap_pool_prediction.append(self.cap_pool)
        self.spot_price_b_prediction.append(self.spot_price_b())
        self.spot_price_a_prediction.append(self.spot_price_a())
        self.nxm_supply_prediction.append(self.nxm_supply)
        self.book_value_prediction.append(self.book_value())
        self.liq_prediction.append(self.liq)
        self.liq_NXM_b_prediction.append(self.liq_NXM_b)
        self.liq_NXM_a_prediction.append(self.liq_NXM_a)
        self.eth_sold_prediction.append(self.eth_sold)
        self.eth_acquired_prediction.append(self.eth_acquired)
        self.nxm_burned_prediction.append(self.nxm_burned)
        self.nxm_minted_prediction.append(self.nxm_minted)

        # increment day
        self.current_day += 1

    def show_metrics(self):
        # print snapshot
        print(f' Capital pool: {self.cap_pool} ETH')
        print(f' Below NXM price: {self.spot_price_b()} ETH')
        print(f' Above NXM price: {self.spot_price_a()} ETH')
        print(f' NXM Supply: {self.nxm_supply}')
        print(f' Book Value: {self.book_value()} ETH')
        print(f' RAMM ETH Liquidity: {self.liq}')
        print(f' Below NXM Reserve: {self.liq_NXM_b}')
        print(f' Above NXM Reserve: {self.liq_NXM_a}')

    def write_metrics(self):
        # add to record
        self.cap_pool_prediction.append(self.cap_pool)
        self.spot_price_b_prediction.append(self.spot_price_b())
        self.spot_price_a_prediction.append(self.spot_price_a())
        self.nxm_supply_prediction.append(self.nxm_supply)
        self.book_value_prediction.append(self.book_value())
        self.liq_prediction.append(self.liq)
        self.liq_NXM_b_prediction.append(self.liq_NXM_b)
        self.liq_NXM_a_prediction.append(self.liq_NXM_a)
        self.eth_sold_prediction.append(self.eth_sold)
        self.eth_acquired_prediction.append(self.eth_acquired)
        self.nxm_burned_prediction.append(self.nxm_burned)
        self.nxm_minted_prediction.append(self.nxm_minted)

        # increment step
        self.steps += 1