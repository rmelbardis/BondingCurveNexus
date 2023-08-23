'''
Define the wNXM Market as a class
This allows us to track the different variables relating to wNXM as they change over time
in a consistent manner.
A market instance can then be used to simulate a wNXM environment
to place external pressures on the RAMM mechanism. 

The market class the following features:
 - Price decreases upon sells and increases upon buys
 - functions allow for removing/adding wNXM to supply or not
 - arbitrage functions that allow for:
    arb_sale_transaction(n_nxm) - buying wNXM, unwrapping and selling to below pool
    arb_buy_transaction(eth) - buying NXM from above pool, wrapping and selling to open market
'''

import numpy as np

from BondingCurveNexus import sys_params, model_params

class wNxmMarket:

    def __init__(self, nxm, ramm, pool, dev):
        
        # takes the contract deployments as arguments,
        # so that we can call solidity functions from within the class 
        self.nxm = nxm
        self.ramm = ramm
        self.pool = pool
        self.dev = dev
        
        # OPENING STATE of market upon initializing a projection instance
        # set opening state of market
        self.wnxm_supply = sys_params.wnxm_supply_now
        self.wnxm_price = sys_params.wnxm_price_now

        # set ETH value for wNXM price shift as a result of 1 ETH of buy/sell
        self.wnxm_move_size = model_params.wnxm_move_size
        self.arb_sale_size_nxm = 1000
        self.arb_buy_size_eth = 21.6
    
    
    # WNXM MARKET FUNCTIONS
    def market_buy(self, n_wnxm, remove=True):
        # limit number of wnxm bought to total supply
        n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole buy happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # increase price depending on defined liquidity parameters
        self.wnxm_price += n_eth * self.wnxm_move_size

        # if used for arb, remove from supply
        if remove:
            self.wnxm_supply -= n_wnxm

    def market_sell(self, n_wnxm, create=True):
        # limit number of wnxm sold to total supply unless new wnxm is created
        if not create:
            n_wnxm = min(n_wnxm, self.wnxm_supply)

        # crude calc for ETH amount (assuming whole sell happens on opening price)
        n_eth = n_wnxm * self.wnxm_price

        # decrease price depending on defined liquidity parameters
        self.wnxm_price -= n_eth * self.wnxm_move_size

        # if used for arb, add to supply (& limit by nxm supply)
        if create:
            self.wnxm_supply = min(self.wnxm_supply + n_wnxm, self.nxm.balanceOf(self.dev)/1e18)

 # daily percentage change in wNXM price
 # represents buys/sells in wnxm market without interacting with protocol
    def shift(self):
        # set percentage changes in wnxm price using a normal distribution
        self.wnxm_price *=  (1 + np.random.normal(loc=model_params.wnxm_drift,
                                                 scale=model_params.wnxm_diffusion)
                            )

    # WNXM-NXM ARBITRAGE TRANSACTION FUNCTIONS
    def arb_sale_transaction(self, n_nxm):
        # establish size of nxm sell, limit to number of nxm supply and wnxm supply
        num = min(n_nxm, self.wnxm_supply, self.nxm.balanceOf(self.dev)/1e18)
        # buy from open market
        self.market_buy(n_wnxm=num, remove=True)
        # sell to protocol
        self.ramm.swap(int(num*1e18), sender=self.dev)

    def arb_buy_transaction(self, eth):
        
        # note current NXM supply
        old_sup = self.nxm.balanceOf(self.dev)/1e18
        
        # buy from protocol
        self.ramm.swap(0, value=int(eth*1e18), sender=self.dev)
        
        # establish nxm obtained
        
        num = self.nxm.balanceOf(self.dev)/1e18 - old_sup
        
        # sell to open market
        self.market_sell(n_wnxm=num, create=True)

    def arbitrage(self):
        # system price > wnxm_price arb
            # protocol sale price has to be higher than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while  self.ramm.getSpotPriceB()/1e18 > self.wnxm_price and \
                self.nxm.balanceOf(self.dev)/1e18 > 0 and self.wnxm_supply > 0:     
            self.arb_sale_transaction(n_nxm=self.arb_sale_size_nxm)

        # system price < wnxm_price arb
            # protocol price has to be lower than wnxm price for arbitrage
            # nxm supply has to be greater than zero
        while self.ramm.getSpotPriceA()/1e18 < self.wnxm_price and \
                self.nxm.balanceOf(self.dev)/1e18 > 0:
            self.arb_buy_transaction(eth=self.arb_buy_size_eth)
