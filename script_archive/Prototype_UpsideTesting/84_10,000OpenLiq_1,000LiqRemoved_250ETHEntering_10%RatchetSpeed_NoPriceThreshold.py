from ape import networks, accounts, project
import click
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os
import shutil
from BondingCurveNexus.sys_params import pool_eth, pool_dai, eth_price_usd, mcr_now, nxm_supply_now
from BondingCurveNexus.model_params import NXM_entry_values


def main():
    
    run_name = "84_10,000OpenLiq_1,000LiqRemoved_250ETHEntering_10%RatchetSpeed_NoPriceThreshold"
    ratchet_speed = 10
    liq_withdrawal = 1000
    
    # eth entries daily and quarter-daily
    daily_eth_entering = NXM_entry_values[1]
    eth_in_per_qday = daily_eth_entering / 4
    
    # threshold above which no-one wants to buy
    threshold = False
    bv_threshold = 1.2
    # for graph title
    if not threshold:
        threshold_input = 'infinite'
    else:
        threshold_input = bv_threshold * 100
    
    # Time to run the simulation for
    quarter_days = 120
    
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

    # Tracking Metrics
    cap_pool_prediction = np.array([pool.getPoolValueInEth()/1e18])
    cap_pool_change_prediction = np.array([cap_pool_prediction[-1] - cap_pool_prediction[0]])
    nxm_supply_prediction = np.array([nxm.balanceOf(dev)/1e18])
    book_value_prediction = np.array([cap_pool_prediction[-1] / nxm_supply_prediction[-1]])
    liq_prediction = np.array([ramm.getReserves()[0]/1e18])
    spot_price_b_prediction = np.array([ramm.getSpotPriceB()/1e18])
    spot_price_a_prediction = np.array([ramm.getSpotPriceA()/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])

    block = networks.provider.get_block('latest')
    times = np.array([(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])
    
    for i in range(quarter_days):

        # MOVE TIME
        print(f'time = {times[-1]}')
        networks.provider.set_timestamp(block.timestamp + 21_600)
        networks.provider.mine()
        block = networks.provider.get_block('latest')

        # SWAP ETH EVERY TIME
        
        # assume swapping only happens if NXM price is above a certain percentage of BV
        if not threshold: 
                ramm.swap(0, value=int(eth_in_per_qday * 1e18), sender=dev)
        else:
            if spot_price_a_prediction[-1] < book_value_prediction[-1] * bv_threshold: 
                ramm.swap(0, value=int(eth_in_per_qday * 1e18), sender=dev)

        # RECORD METRICS & TIME

        times = np.append(times, [(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])

        cap_pool_prediction = np.append(cap_pool_prediction, [pool.getPoolValueInEth()/1e18])
        cap_pool_change_prediction = np.append(cap_pool_change_prediction, [cap_pool_prediction[-1] - cap_pool_prediction[0]])
        nxm_supply_prediction = np.append(nxm_supply_prediction, [nxm.balanceOf(dev)/1e18])
        book_value_prediction = np.append(book_value_prediction, [cap_pool_prediction[-1] / nxm_supply_prediction[-1]])
        liq_prediction = np.append(liq_prediction, [ramm.getReserves()[0]/1e18])
        spot_price_b_prediction = np.append(spot_price_b_prediction, [ramm.getSpotPriceB()/1e18])
        spot_price_a_prediction = np.append(spot_price_a_prediction, [ramm.getSpotPriceA()/1e18])
        liq_NXM_b_prediction = np.append(liq_NXM_b_prediction, [ramm.getReserves()[2]/1e18])
        liq_NXM_a_prediction = np.append(liq_NXM_a_prediction, [ramm.getReserves()[1]/1e18])

    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(3, 2, figsize=(15,18))
    fig.suptitle(f'''Deterministic Protocol-only Model, Solidity Contracts
                 Opening and target liq of {liq_prediction[0]} ETH
                 Ratchet speed = {ratchet_speed}% of BV/day. Max daily liquidity withdrawal of {liq_withdrawal} ETH.
                 Testing {daily_eth_entering} ETH entering/day as long as price is no more than {threshold_input}% of BV
                 ''',
                 fontsize=16)
    # fig.tight_layout()
    fig.subplots_adjust(top=0.88)

    # Subplot
    axs[0, 0].plot(times, spot_price_b_prediction, label='price below')
    axs[0, 0].plot(times, spot_price_a_prediction, label='price above')
    axs[0, 0].plot(times, book_value_prediction, label='book value')
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(times, cap_pool_prediction)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].plot(times, nxm_supply_prediction, label='nxm')
    axs[1, 0].set_title('nxm_supply')
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
    # Subplot
    axs[2, 1].plot(times, cap_pool_change_prediction)
    axs[2, 1].set_title('capital_captured')

    fig.savefig('graphs/graph.png')

    #-----COPY + RENAME SCRIPT AND GRAPH-----#
    src_dir = os.getcwd() # get the current working dir

    # copy graph
    graph_dest_dir = src_dir + "/graphs/upside_testing"
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
    script_dest_dir = src_dir + "/script_archive/UpsideTesting"
    script_src_file = os.path.join(src_dir, "scripts", "sim.py")
    # copy the file to destination dir
    shutil.copy(script_src_file , script_dest_dir) 

    # rename the file
    script_dest_file = os.path.join(script_dest_dir, 'sim.py')
    new_script_file_name = os.path.join(script_dest_dir, f'{run_name}.py')

    os.rename(script_dest_file, new_script_file_name) # rename
    
    print(f'script copied to {new_script_file_name}')
