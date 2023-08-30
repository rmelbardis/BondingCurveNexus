from ape import networks, accounts, project
import click
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os
import shutil
from random import shuffle
from BondingCurveNexus.sys_params import pool_eth, pool_dai, eth_price_usd, mcr_now, nxm_supply_now
from BondingCurveNexus.model_params import wnxm_drift, wnxm_diffusion, wnxm_move_size, lambda_entries, lambda_exits
from BondingCurveNexus.wNXM_Market import wNxmMarket


def main():
    
    run_name = "ProtOnly_10,000TarLiq_100LiqIn_100LiqOut_2%Ratchet_100ETHEntriesDay_0ExitsDay"
    # eth_reserve = 43_835
    
    # Time to run the simulation for
    days = 100
    interval_seconds = 24 * 3600
    
    # NXM total exit force total and per quarter-day assuming they all want to exit within a month
    # initial_nxm_exiting = NXM_exit_values[3]
    # remaining_nxm_exiting = initial_nxm_exiting
    # nxm_out_per_qday = initial_nxm_exiting / (4 * 365 / 12)
    # # threshold below which no-one wants to sell
    # bv_threshold = 0.95
    
    ecosystem_name = networks.provider.network.ecosystem.name
    network_name = networks.provider.network.name
    provider_name = networks.provider.name
    click.echo(f"You are connected to network '{ecosystem_name}:{network_name}:{provider_name}'.")

    click.echo(f"Deploying contracts")
    dev = accounts.test_accounts[0]
    dev.balance = int(1e27)

    nxm = dev.deploy(project.NXM)
    nxm.mint(dev, int(nxm_supply_now * 1e18), sender=dev)

    pool = dev.deploy(project.CapitalPool, int(pool_dai * 1e18), int(1e18 // eth_price_usd), int(mcr_now * 1e18), value=int(pool_eth*1e18))
    ramm = dev.deploy(project.Ramm, nxm.address, pool.address)

    wnxm = wNxmMarket(nxm, ramm, pool, dev)

    # Tracking Metrics
    cap_pool_prediction = np.array([pool.getPoolValueInEth()/1e18])
    nxm_supply_prediction = np.array([nxm.balanceOf(dev)/1e18])
    book_value_prediction = np.array([cap_pool_prediction[-1] / nxm_supply_prediction[-1]])
    liq_prediction = np.array([ramm.getReserves()[0]/1e18])
    spot_price_b_prediction = np.array([ramm.getSpotPriceB()/1e18])
    spot_price_a_prediction = np.array([ramm.getSpotPriceA()/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])
    # nxm_exiting_prediction = np.array([remaining_nxm_exiting])
    # wnxm_price_prediction = np.array([wnxm.wnxm_price])
    # wnxm_supply_prediction = np.array([wnxm.wnxm_supply])

    block = networks.provider.get_block('latest')
    times = np.array([(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])
    
    for i in range(days):

        # MOVE TIME
        print(f'time = {times[-1]}')
        networks.provider.set_timestamp(block.timestamp + interval_seconds)
        networks.provider.mine()
        block = networks.provider.get_block('latest')

        # RECORD METRICS & TIME

        times = np.append(times, [(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])

        cap_pool_prediction = np.append(cap_pool_prediction, [pool.getPoolValueInEth()/1e18])
        nxm_supply_prediction = np.append(nxm_supply_prediction, [nxm.balanceOf(dev)/1e18])
        book_value_prediction = np.append(book_value_prediction, [cap_pool_prediction[-1] / nxm_supply_prediction[-1]])
        liq_prediction = np.append(liq_prediction, [ramm.getReserves()[0]/1e18])
        spot_price_b_prediction = np.append(spot_price_b_prediction, [ramm.getSpotPriceB()/1e18])
        spot_price_a_prediction = np.append(spot_price_a_prediction, [ramm.getSpotPriceA()/1e18])
        liq_NXM_b_prediction = np.append(liq_NXM_b_prediction, [ramm.getReserves()[2]/1e18])
        liq_NXM_a_prediction = np.append(liq_NXM_a_prediction, [ramm.getReserves()[1]/1e18])
        # nxm_exiting_prediction = np.append(nxm_exiting_prediction, [remaining_nxm_exiting])
        # wnxm_price_prediction = np.append(wnxm_price_prediction, [wnxm.wnxm_price])
        # wnxm_supply_prediction = np.append(wnxm_supply_prediction, [wnxm.wnxm_supply])
                
        events_today = []
        events_today.extend(['buy'] * lambda_entries)
        events_today.extend(['sale'] * lambda_exits)
        shuffle(events_today)
        
        for e in events_today:
            # wnxm.arbitrage()
            if e == 'buy':
                # if ramm.getSpotPriceA()/1e18 > wnxm.wnxm_price and wnxm.wnxm_supply > 0:
                #     wnxm.market_buy(n_wnxm = wnxm.arb_buy_size_eth / wnxm.wnxm_price, remove=False)
                # else:
                ramm.swap(0, value=int(wnxm.arb_buy_size_eth * 1e18), sender=dev)
                
            if e == 'sale':
                # if ramm.getSpotPriceB()/1e18 < wnxm.wnxm_price:
                #     wnxm.market_sell(n_wnxm=wnxm.arb_sale_size_nxm)
                # else:
                ramm.swap(wnxm.arb_sale_size_nxm, sender=dev)
        
        # SWAP NXM EVERY TIME
        
        # assume swapping only happens if NXM price > 95% of BV
        
        # if ramm.getSpotPriceB()/1e18 > (pool.getPoolValueInEth() * bv_threshold / nxm.balanceOf(dev)) and \
        #     remaining_nxm_exiting > 0: 
        #         ramm.swap(int(min(remaining_nxm_exiting, nxm_out_per_qday) * 1e18), sender=dev)
        #         remaining_nxm_exiting = max(remaining_nxm_exiting - nxm_out_per_qday, 0)

        # WNXM ARBITRAGE
        # wnxm.shift()
        # wnxm.arbitrage()

        # SWAP ETH EVERY TIME
        
        # eth_amount = 10
        # ramm.swap(0, value=int(eth_amount * 1e18), sender=dev)
    
    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(3, 2, figsize=(15,18))
    fig.suptitle(f'''Deterministic Protocol Model, Solidity Contracts
                 Target liq of {liq_prediction[0]} ETH. Ratchet speed = 2% of BV/day.
                 Liq withdrawal of 100 ETH/day and long-term liq injection at 100 ETH/day
                 {lambda_exits} {wnxm.arb_sale_size_nxm} NXM exits per day. {lambda_entries} {wnxm.arb_buy_size_eth} ETH entries per day.
                 ''',
                 fontsize=16)
    # fig.tight_layout()
    fig.subplots_adjust(top=0.90)

    # Subplot
    axs[0, 0].plot(times, spot_price_b_prediction, label='price below')
    axs[0, 0].plot(times, spot_price_a_prediction, label='price above')
    axs[0, 0].plot(times, book_value_prediction, label='book value')
    # axs[0, 0].plot(times, wnxm_price_prediction, label='wnxm price')
    axs[0, 0].set_title('prices')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(times, cap_pool_prediction)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].plot(times, nxm_supply_prediction, label='nxm')
    # axs[1, 0].plot(times, wnxm_supply_prediction, label='wnxm')
    axs[1, 0].set_title('token_supply')
    axs[1, 0].legend()
    # Subplot
    axs[1, 1].plot(times, liq_NXM_b_prediction, label='NXM reserve below')
    axs[1, 1].plot(times, liq_NXM_a_prediction, label='NXM reserve above')
    axs[1, 1].set_title('liquidity_nxm')
    axs[1, 1].legend()
    # Subplot
    axs[2, 0].plot(times, liq_prediction, label='ETH liquidity')
    axs[2, 0].plot(times, np.full(shape=len(times), fill_value=liq_prediction[0]), label='target')
    axs[2, 0].set_title('liquidity_eth')
    axs[2, 0].legend()

    fig.savefig('graphs/graph.png')

    #-----COPY + RENAME SCRIPT AND GRAPH-----#
    src_dir = os.getcwd() # get the current working dir

    # copy graph
    graph_dest_dir = src_dir + "/graphs/liquidity_discussion_runs/stage_2"
    graph_src_file = os.path.join(src_dir, "graphs", "graph.png")
    # copy the file to destination dir
    shutil.copy(graph_src_file , graph_dest_dir) 

    # rename the file
    graph_dest_file = os.path.join(graph_dest_dir, 'graph.png')
    new_graph_file_name = os.path.join(graph_dest_dir, f'{run_name}.png')

    os.rename(graph_dest_file, new_graph_file_name)
    
    # print message that it's happened
    print(f'graph copied to {new_graph_file_name}')
    
    # copy script
    script_dest_dir = src_dir + "/script_archive/LiqStage2Sims"
    script_src_file = os.path.join(src_dir, "scripts", "sim.py")
    # copy the file to destination dir
    shutil.copy(script_src_file , script_dest_dir) 

    # rename the file
    script_dest_file = os.path.join(script_dest_dir, 'sim.py')
    new_script_file_name = os.path.join(script_dest_dir, f'{run_name}.py')

    os.rename(script_dest_file, new_script_file_name) # rename
    
    print(f'script copied to {new_script_file_name}')
