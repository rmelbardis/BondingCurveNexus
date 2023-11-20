from ape import networks, accounts, Contract
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os
import shutil
import json
from BondingCurveNexus.model_params import NXM_exit_values


def main():
    
    # snapshot the current state and reset to the start for every run
    # name the file to write snapshot id to
    snapshot_file = "./deployment/snapshot.json"
    
    # try to open the snapshot file and revert to snapshot
    try:
        with open(snapshot_file, 'r') as file:
            snapshot = json.load(file)
            networks.provider.revert(snapshot)
    
    # if no snapshot exists, except
    except Exception as error:
        print("An error occured:", error)
    
    # take snapshot of current state    
    snapshot = networks.provider.snapshot()
    # write snapshot id into json file
    with open(snapshot_file, 'w') as file:
        json.dump(snapshot, file)
    
    # load addresses file into dictionary
    addresses_file = "./deployment/addresses.json"
    with open(addresses_file, 'r') as file:
      addresses = json.load(file)

    # define dev account and load up with lots of ETH
    dev = accounts.test_accounts[0]
    dev.balance = int(1e27)
    
    # define ep
    # ep_multisig = accounts["0x422D71fb8040aBEF53f3a05d21A9B85eebB2995D"]
    # ep_multisig.balance = int(1e27)
    
    # define constants for addresses
    TC = addresses.get('TokenController')
    NXM = addresses.get('NXMToken')
    POOL = addresses.get('Pool')
    RAMM = addresses.get('Ramm')

    
    # initialize contracts
    nxm = Contract(NXM, abi="./deployment/abis/NXMToken.json")
    pool = Contract(POOL, abi="./deployment/abis/Pool.json")
    ramm = Contract(RAMM, abi="./deployment/abis/Ramm.json")
    
    # dev gives permission to TokenController to use NXM
    nxm.approve(TC, 2 ** 256 - 1, sender=dev)
    
    # ep multisig turns off circuit breakers
    ramm.setCircuitBreakerLimits(2 ** 32 - 1, 2 ** 32 - 1, sender=dev)
    
    # set the block base fee to 0 and impersonate TokenController to make a call
    # networks.provider._make_request("hardhat_setNextBlockBaseFeePerGas", ['0x0'])
    # nxm.mint(dev, int(1e18), sender=TC)

    # print some initial variables - NXM supply and Capital Pool
    print (f'NXM supply = {nxm.totalSupply() / 1e18}')
    print (f'NXM Dev balance = {nxm.balanceOf(dev) / 1e18}')
    print (f'Pool value in ETH = {pool.getPoolValueInEth() / 1e18}')
    

    block = networks.provider.get_block('latest')
    times = np.array([(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now())
                      / datetime.timedelta(days=1)])
    
    run_name = "07_4,056,000NXMExiting"
    
    # set nxm exits monthly, daily and quarter-daily
    initial_nxm_exiting = NXM_exit_values[6]
    remaining_nxm_exiting = initial_nxm_exiting
    
    daily_nxm_exiting = initial_nxm_exiting / 30.417
    nxm_out_per_qday = daily_nxm_exiting / 4
    print(f'nxm out every quarter day = {nxm_out_per_qday}')
    
    # variables only used for graph header 
    ratchet_speed = 4
    fast_ratchet_speed = 50 
    fast_liq_injection = 1500
    liq_injection = 100

    # threshold above which no-one wants to sell & whether enabled
    threshold = True
    bv_threshold = 0.95
    # for graph title
    if not threshold:
        threshold_input = 0
    else:
        threshold_input = bv_threshold * 100
    
    # Time to run the simulation for
    quarter_days = 365
    
    # Tracking Metrics
    cap_pool_prediction = np.array([pool.getPoolValueInEth()/1e18])
    cap_pool_change_prediction = np.array([cap_pool_prediction[0] - cap_pool_prediction[-1]])
    nxm_supply_prediction = np.array([nxm.totalSupply()/1e18])
    book_value_prediction = np.array([ramm.getBookValue()/1e18])
    liq_prediction = np.array([ramm.getReserves()[0]/1e18])
    spot_price_b_prediction = np.array([ramm.getSpotPrices()[1]/1e18])
    spot_price_a_prediction = np.array([ramm.getSpotPrices()[0]/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])
    budget_prediction = np.array([ramm.getReserves()[3]/1e18])
    ip_prediction = np.array([ramm.getInternalPrice()/1e18])
    nxm_exiting_prediction = np.array([remaining_nxm_exiting])
    
    # MAIN TIME LOOP
    for i in range(quarter_days):

        # MOVE TIME
        print(f'time = {times[-1]}')
        networks.provider.set_timestamp(block.timestamp + 21_600)
        networks.provider.mine()
        block = networks.provider.get_block('latest')

        # SWAP ETH EVERY TIME
        
        # print metrics
        print(f'before swap pool = {cap_pool_prediction[-1]}')
        print(f'before swap supply = {nxm_supply_prediction[-1]}')
        print(f'before swap BV = {book_value_prediction[-1]}')
        print(f'before swap liq = {liq_prediction[-1]}')
        print(f'before swap spot_b = {spot_price_b_prediction[-1]}')
        print(f'before swap spot_a = {spot_price_a_prediction[-1]}')
        print(f'before swap NXM_b = {liq_NXM_b_prediction[-1]}')
        print(f'before swap NXM_a = {liq_NXM_a_prediction[-1]}')
        print(f'before swap budget = {budget_prediction[-1]}')
        print(f'before swap ip = {ip_prediction[-1]}')
        print(f'before swap nxm exiting = {nxm_exiting_prediction[-1]}')
        
        # assume swapping only happens if all NXM exiting has already exited
        if remaining_nxm_exiting > 0:
        # swap if NXM price is above a threshold percentage of BV or if threshold is disabled
            if not threshold: 
                    ramm.swap(int(min(nxm_out_per_qday, remaining_nxm_exiting)*1e18), 0, 32503680000, sender=dev)
                    remaining_nxm_exiting = max(remaining_nxm_exiting - nxm_out_per_qday, 0)
            else:
                if ramm.getSpotPrices()[1] > ramm.getBookValue() * bv_threshold: 
                    ramm.swap(int(min(nxm_out_per_qday, remaining_nxm_exiting)*1e18), 0, 32503680000, sender=dev)
                    remaining_nxm_exiting = max(remaining_nxm_exiting - nxm_out_per_qday, 0)
        
        # RECORD METRICS & TIME

        times = np.append(times, [(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now())
                                  / datetime.timedelta(days=1)])

        cap_pool_prediction = np.append(cap_pool_prediction, [pool.getPoolValueInEth()/1e18])
        cap_pool_change_prediction = np.append(cap_pool_change_prediction, [cap_pool_prediction[0] - cap_pool_prediction[-1]])
        nxm_supply_prediction = np.append(nxm_supply_prediction, [nxm.balanceOf(dev)/1e18])
        book_value_prediction = np.append(book_value_prediction, [ramm.getBookValue()/1e18])
        liq_prediction = np.append(liq_prediction, [ramm.getReserves()[0]/1e18])
        spot_price_b_prediction = np.append(spot_price_b_prediction, [ramm.getSpotPrices()[1]/1e18])
        spot_price_a_prediction = np.append(spot_price_a_prediction, [ramm.getSpotPrices()[0]/1e18])
        liq_NXM_b_prediction = np.append(liq_NXM_b_prediction, [ramm.getReserves()[2]/1e18])
        liq_NXM_a_prediction = np.append(liq_NXM_a_prediction, [ramm.getReserves()[1]/1e18])
        budget_prediction = np.append(budget_prediction, [ramm.getReserves()[3]/1e18])
        ip_prediction = np.append(ip_prediction, [ramm.getInternalPrice()/1e18])
        nxm_exiting_prediction = np.append(nxm_exiting_prediction, [remaining_nxm_exiting])
        
        print(f'after swap pool = {cap_pool_prediction[-1]}')
        print(f'after swap supply = {nxm_supply_prediction[-1]}')
        print(f'after swap BV = {book_value_prediction[-1]}')
        print(f'after swap liq = {liq_prediction[-1]}')
        print(f'after swap spot_b = {spot_price_b_prediction[-1]}')
        print(f'after swap spot_a = {spot_price_a_prediction[-1]}')
        print(f'after swap NXM_b = {liq_NXM_b_prediction[-1]}')
        print(f'after swap NXM_a = {liq_NXM_a_prediction[-1]}')
        print(f'after swap budget = {budget_prediction[-1]}')
        print(f'after swap ip = {ip_prediction[-1]}')
        print(f'after swap nxm exiting = {nxm_exiting_prediction[-1]}')
          
    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(3, 2, figsize=(15,18))
    fig.suptitle(f'''Deterministic Protocol-only Model, Solidity Contracts
                 Opening and target liq of {liq_prediction[0]} ETH; Budget of {budget_prediction[0]} ETH
                 Ratchet speed while budget lasts = {fast_ratchet_speed}% of BV/day; {ratchet_speed}% of BV/day after
                 Max daily liquidity injection of {fast_liq_injection} ETH while budget lasts and {liq_injection} ETH after 
                 Testing {nxm_exiting_prediction[0]} NXM exiting over at least a month and as long as price is more than {threshold_input}% of BV
                 ''',
                 fontsize=16)
    # fig.tight_layout()
    fig.subplots_adjust(top=0.88)

    # Subplot
    axs[0, 0].plot(times, spot_price_b_prediction, label='price below')
    axs[0, 0].plot(times, spot_price_a_prediction, label='price above')
    axs[0, 0].plot(times, book_value_prediction, label='book value')
    axs[0, 0].plot(times, ip_prediction, label='internal price')
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(times, cap_pool_prediction)
    axs[0, 1].set_title('cap_pool')
    # Subplot
    axs[1, 0].plot(times, nxm_supply_prediction, label='nxm supply')
    axs[1, 0].plot(times, nxm_exiting_prediction, label='nxm exiting')
    axs[1, 0].set_title('nxm_supply')
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
    # Subplot
    axs[2, 1].plot(times, cap_pool_change_prediction, label='capital_loss')
    axs[2, 1].plot(times, budget_prediction, label='budget')
    axs[2, 1].set_title('capital_loss')
    axs[2, 1].legend()

    fig.savefig('graphs/graph.png')

    #-----COPY + RENAME SCRIPT AND GRAPH-----#
    src_dir = os.getcwd() # get the current working dir

    # copy graph
    graph_dest_dir = src_dir + "/graphs/implementation_initial_state_testing"
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
    script_dest_dir = src_dir + "/script_archive/Implementation_Initial_State"
    script_src_file = os.path.join(src_dir, "scripts", "sim.py")
    # copy the file to destination dir
    shutil.copy(script_src_file , script_dest_dir)

    # rename the file
    script_dest_file = os.path.join(script_dest_dir, 'sim.py')
    new_script_file_name = os.path.join(script_dest_dir, f'{run_name}.py')

    os.rename(script_dest_file, new_script_file_name) # rename

    print(f'script copied to {new_script_file_name}')
