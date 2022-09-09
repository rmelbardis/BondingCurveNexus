'''
Define the Nexus Mutual system as a class
This allows us to track the different variables as they change over time
in a consistent manner.
Buying and selling mechanism is a virtual Uni v2 pool
'''

from scipy.stats import lognorm
import numpy as np
from random import shuffle

from BondingCurveNexus import sys_params, model_params, param_functions

class NexusSystem:

    def __init__(self, liquidity_eth, wnxm_move_size):
        # OPENING STATE of system upon initializing a projection instance
        # start at day 0
        self.current_day = 0
        # set current state of system
        self.act_cover = sys_params.act_cover_now
        self.nxm_supply = sys_params.nxm_supply_now
        self.wnxm_supply = sys_params.wnxm_supply_now
        self.cap_pool = sys_params.cap_pool_now
        self.wnxm_price = sys_params.wnxm_price_now

        # set ETH value for wNXM price shift as a result of 1 ETH of buy/sell
        self.wnxm_move_size = wnxm_move_size

        # OPENING STATE of virtual uni pool
        # set initial ETH liquidity as initial parameter
        self.liquidity_eth = liquidity_eth
        # set initial NXM liquidity based on opening wnxm price
        # in practice we can start much lower than wnxm price (as we won't necessarily have an oracle)
        # but for simulation purposes this is the first interesting point
        self.liquidity_nxm = self.liquidity_eth / self.wnxm_price
        # set initial invariant
        self.invariant = self.liquidity_eth * self.liquidity_nxm

        # create RANDOM VARIABLE ARRAYS for individual projection
        # base non-arb entries and exits using a poisson distribution
        self.base_daily_platform_buys = np.random.poisson(
                                                lam=model_params.lambda_entries,
                                                size=model_params.model_days)
        self.base_daily_platform_sales = np.random.poisson(
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

        # daily randomised values between 0 and 1 to check vs claim occurence probability
        self.claim_rolls = np.random.random(size = model_params.model_days)

        # set cumulative counters to zero
        self.cum_premiums = 0
        self.cum_claims = 0
        self.cum_investment = 0
        self.eth_sold = 0
        self.eth_acquired = 0
        self.nxm_burned = 0
        self.nxm_minted = 0
        self.wnxm_removed = 0
        self.wnxm_created = 0

        # create tracking lists for individual instance
        self.mcr_prediction = [self.mcr()] #1
        self.act_cover_prediction = [self.act_cover] #2
        self.cap_pool_prediction = [self.cap_pool] #3
        self.mcrp_prediction = [self.mcrp()] #4
        self.nxm_price_prediction = [self.nxm_price()] #5
        self.wnxm_price_prediction = [self.wnxm_price] #6
        self.liquidity_nxm_prediction = [self.liquidity_nxm] #7
        self.liquidity_eth_prediction = [self.liquidity_eth]  #8
        self.nxm_supply_prediction = [self.nxm_supply] #9
        self.wnxm_supply_prediction = [self.wnxm_supply] #10
        self.book_value_prediction = [self.book_value()] #11
        self.cum_premiums_prediction = [self.cum_premiums] #12
        self.cum_claims_prediction = [self.cum_claims] #13
        self.cum_investment_prediction = [self.cum_investment] #14
        self.eth_sold_prediction = [self.eth_sold] #15
        self.eth_acquired_prediction = [self.eth_acquired] #16
        self.nxm_burned_prediction = [self.nxm_burned] #17
        self.nxm_minted_prediction = [self.nxm_minted] #18
        self.wnxm_removed_prediction = [self.wnxm_removed] #19
        self.wnxm_created_prediction = [self.wnxm_created] #20

    # INSTANCE FUNCTIONS
    # to calculate a variety of ongoing metrics & parameters
    # and update the system accordingly

    # calculate mcr from current cover amount
    # minimum of 0.01 ETH to avoid division by zero
    def mcr(self):
        return max(0.01, self.act_cover / sys_params.capital_factor)

    # calculate mcr% from current assets and mcr size.
    def mcrp(self):
        return min(20, self.cap_pool/self.mcr())

    # calculate book value from current assets & nxm supply.
    def book_value(self):
        if self.nxm_supply == 0:
            return 0
        return self.cap_pool/self.nxm_supply

    # calculate system nxm price from virtual Uni v2-style pool
    def nxm_price(self):
        return self.liquidity_eth / self.liquidity_nxm

    # function to determine the random sizing of a buy/sell interaction
    # either with platform or wNXM market
    def nxm_sale_size(self, denom='nxm'):
        if denom == 'nxm':
            return lognorm.rvs(s=model_params.exit_shape,
                               loc=model_params.exit_loc,
                               scale=model_params.exit_scale) / self.nxm_price()
        elif denom == 'eth':
            return lognorm.rvs(s=model_params.exit_shape,
                               loc=model_params.exit_loc,
                               scale=model_params.exit_scale)

    # one sale of n_nxm NXM
    def platform_nxm_sale(self, n_nxm):
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

        # update ETH liquidity
        self.liquidity_eth = new_eth

    def platform_nxm_buy(self, n_nxm):
        # remove bought NXM and add to supply
        self.liquidity_nxm -= n_nxm
        self.nxm_supply += n_nxm

        # establish new value of eth in pool
        new_eth = self.invariant / self.liquidity_nxm
        delta_eth = new_eth - self.liquidity_eth

        # add ETH removed and nxm burned to cumulative total, update capital pool
        self.eth_acquired += delta_eth
        self.cap_pool += delta_eth
        self.nxm_minted += n_nxm

        # update ETH liquidity
        self.liquidity_eth = new_eth

    def wnxm_market_buy(self, n_wnxm, arb=True):
        # limit number of wnxm bought to total supply
        n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole buy happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # increase price depending on defined liquidity parameters
        self.wnxm_price += n_eth * self.wnxm_move_size

        # if used for arb, remove from supply
        if arb:
            self.wnxm_supply -= n_wnxm
            self.wnxm_removed += n_wnxm

    def wnxm_market_sell(self, n_wnxm, arb=True):
        # limit number of wnxm bought to total supply
        n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole sell happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # decrease price depending on defined liquidity parameters
        self.wnxm_price -= n_eth * self.wnxm_move_size

        # if used for arb, add to supply
        if arb:
            self.wnxm_supply += n_wnxm
            self.wnxm_created += n_wnxm

    def arb_sale_transaction(self):
        # establish size of nxm sell
        num = self.nxm_sale_size(denom='nxm')
        # buy from open market
        self.wnxm_market_buy(n_wnxm=num, arb=True)
        # sell to platform
        self.platform_nxm_sale(n_nxm=num)

    def arb_buy_transaction(self):
        # establish size of nxm sell
        num = self.nxm_sale_size(denom='nxm')
        # buy from platform
        self.platform_nxm_buy(n_nxm=num)
        # sell to open market
        self.wnxm_market_sell(n_wnxm=num, arb=True)

    def ratchet_up(self, num, kind='nxm'):
        if kind == 'nxm':
            self.liquidity_nxm -= num
        elif kind == 'eth':
            self.liquidity_eth += num

        self.invariant = self.liquidity_eth * self.liquidity_nxm

    def ratchet_down(self, num, kind='nxm'):
        if kind == 'nxm':
            self.liquidity_nxm += num
        elif kind == 'eth':
            self.liquidity_eth -= num

        self.invariant = self.liquidity_eth * self.liquidity_nxm

    # daily percentage change in wNXM price
    def wnxm_shift(self):
        self.wnxm_price *= (1 + np.random.normal(loc=model_params.wnxm_drift,
                                                 scale=model_params.wnxm_diffusion)
                            )

    # daily percentage change in active cover amount
    def cover_amount_shift(self):
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
        events_today.extend(['ratchet'])
        events_today.extend(['platform_buy'] * self.base_daily_platform_buys[self.current_day])
        events_today.extend(['platform_sale'] * self.base_daily_platform_sales[self.current_day])
        events_today.extend(['wnxm_shift'])
        events_today.extend(['premium_income'])
        events_today.extend(['claim_outgo'])
        events_today.extend(['cover_amount_change'])
        events_today.extend(['investment_return'])
        shuffle(events_today)

        # LOOP THROUGH EVENTS OF DAY
        for event in events_today:

            #-----WNXM ARBITRAGE-----#
            # happens in between all events
            while min(self.nxm_price(), self.book_value()) > self.wnxm_price:
                self.arb_sale_transaction()
            while max(self.nxm_price(), self.book_value()) < self.wnxm_price:
                self.arb_buy_transaction()

            #-----RATCHET-----#
            if event == 'ratchet':
                # up if below BV
                if self.book_value() > self.nxm_price():
                    self.ratchet_up(num=sys_params.ratchet_up_perc*self.liquidity_nxm, kind='nxm')
                # down if above BV
                elif self.book_value() < self.nxm_price():
                    self.ratchet_down(num=sys_params.ratchet_down_perc*self.liquidity_nxm, kind='nxm')

            #-----PLATFORM BUY-----#
            # not arbitrage-driven
            elif event == 'platform_buy':
                # doesn't happen if wnxm price is below platform price or book value
                if max(self.nxm_price(), self.book_value()) > self.wnxm_price:
                    continue
                # otherwise execute the buy
                self.platform_nxm_buy(n_nxm=self.nxm_sale_size())

            #-----PLATFORM SALE-----#
            # not arbitrage-driven
            elif event == 'platform_sale':
                # doesn't happen if wnxm price is above platform price or book value
                if min(self.nxm_price(), self.book_value()) < self.wnxm_price:
                    continue
                # otherwise execute the sell
                self.platform_nxm_sale(n_nxm=self.nxm_sale_size())

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

            #-----INVESTMENT RETURN-----#
            elif event == 'investment_return':
                self.investment_return()

        # append values to tracking metrics
        self.mcr_prediction.append(self.mcr()) #1
        self.act_cover_prediction.append(self.act_cover) #2
        self.cap_pool_prediction.append(self.cap_pool) #3
        self.mcrp_prediction.append(self.mcrp()) #4
        self.nxm_price_prediction.append(self.nxm_price()) #5
        self.wnxm_price_prediction.append(self.wnxm_price) #6
        self.liquidity_nxm_prediction.append(self.liquidity_nxm) #7
        self.liquidity_eth_prediction.append(self.liquidity_eth) #8
        self.nxm_supply_prediction.append(self.nxm_supply) #9
        self.wnxm_supply_prediction.append(self.wnxm_supply) #10
        self.book_value_prediction.append(self.book_value()) #11
        self.cum_premiums_prediction.append(self.cum_premiums) #12
        self.cum_claims_prediction.append(self.cum_claims) #13
        self.cum_investment_prediction.append(self.cum_investment) #14
        self.eth_sold_prediction.append(self.eth_sold) #15
        self.eth_acquired_prediction.append(self.eth_acquired) #16
        self.nxm_burned_prediction.append(self.nxm_burned) #17
        self.nxm_minted_prediction.append(self.nxm_minted) #18
        self.wnxm_removed_prediction.append(self.wnxm_removed) #19
        self.wnxm_created_prediction.append(self.wnxm_created) #20

        # increment day
        self.current_day += 1
