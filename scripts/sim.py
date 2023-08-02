from ape import networks, accounts, project
import click
import numpy as np
import matplotlib.pyplot as plt
import datetime
from BondingCurveNexus.sys_params import pool_eth, pool_dai, eth_price_usd, mcr_now, nxm_supply_now


def main():
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
    book_value_prediction = np.array([pool.getPoolValueInEth() / nxm.balanceOf(dev)])
    nxm_supply_prediction = np.array([nxm.balanceOf(dev)/1e18])
    liq_prediction = np.array([ramm.getReserves()[0]/1e18])
    spot_price_b_prediction = np.array([ramm.getSpotPriceB()/1e18])
    spot_price_a_prediction = np.array([ramm.getSpotPriceA()/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])

    block = networks.provider.get_block('latest')
    times = np.array([(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])

    # Number of hours to run the simulation for
    hours = 1440
    for i in range(hours):

        # MOVE TIME
        print(f'time = {times[-1]}')
        print(f'liquidity = {liq_prediction[-1]}')
        networks.provider.set_timestamp(block.timestamp + 3600)
        networks.provider.mine()
        block = networks.provider.get_block('latest')

        # SWAP NXM EVERY HOUR

        nxm_amount = 500
        ramm.swap(int(nxm_amount * 1e18), sender=dev)

        # RECORD METRICS & TIME

        times = np.append(times, [(datetime.datetime.fromtimestamp(block.timestamp) - datetime.datetime.now()) / datetime.timedelta(days=1)])

        cap_pool_prediction = np.append(cap_pool_prediction, [pool.getPoolValueInEth()/1e18])
        book_value_prediction = np.append(book_value_prediction, [pool.getPoolValueInEth() / nxm.balanceOf(dev)])
        nxm_supply_prediction = np.append(nxm_supply_prediction, [nxm.balanceOf(dev)/1e18])
        liq_prediction = np.append(liq_prediction, [ramm.getReserves()[0]/1e18])
        spot_price_b_prediction = np.append(spot_price_b_prediction, [ramm.getSpotPriceB()/1e18])
        spot_price_a_prediction = np.append(spot_price_a_prediction, [ramm.getSpotPriceA()/1e18])
        liq_NXM_b_prediction = np.append(liq_NXM_b_prediction, [ramm.getReserves()[2]/1e18])
        liq_NXM_a_prediction = np.append(liq_NXM_a_prediction, [ramm.getReserves()[1]/1e18])

    #-----GRAPHS-----#
    # Destructuring initialization
    fig, axs = plt.subplots(3, 2, figsize=(15,18))
    fig.suptitle(f'''Deterministic Protocol-only Model
                 Opening liq of {liq_prediction[0]} ETH and Target liq of {liq_prediction[0]} ETH
                 Initial liquidity movement/day resulting in max of 1000 ETH injection. Withdrawal and long-term injection at 100 ETH/day
                 500-NXM-exits/hour
                 ''',
                 fontsize=16)
    # fig.tight_layout()
    fig.subplots_adjust(top=0.92)

    # Subplot
    axs[0, 0].plot(times, spot_price_b_prediction, label='price below')
    axs[0, 0].plot(times, spot_price_a_prediction, label='price above')
    axs[0, 0].set_title('nxm_price')
    axs[0, 0].legend()
    # Subplot
    axs[0, 1].plot(times, book_value_prediction)
    axs[0, 1].set_title('book_value')
    # Subplot
    axs[1, 0].plot(times, cap_pool_prediction)
    axs[1, 0].set_title('cap_pool')
    # Subplot
    axs[1, 1].plot(times, nxm_supply_prediction, label='nxm')
    axs[1, 1].set_title('nxm_supply')
    # Subplot
    axs[2, 0].plot(times, liq_NXM_b_prediction, label='NXM reserve below')
    axs[2, 0].plot(times, liq_NXM_a_prediction, label='NXM reserve above')
    axs[2, 0].set_title('liquidity_nxm')
    axs[2, 0].legend()
    # Subplot
    axs[2, 1].plot(times, liq_prediction, label='ETH liquidity')
    axs[2, 1].plot(times, np.full(shape=len(times), fill_value=liq_prediction[0]), label='target')
    axs[2, 1].set_title('liquidity_eth')
    axs[2, 1].legend()

    fig.savefig('graphs/graph.png')

    # print(f'price post-swap: {spot_price_b_prediction[1]}')
    # print(f'price impact - {100 * (spot_price_b_prediction[1] - spot_price_b_prediction[0]) / spot_price_b_prediction[0]}%')
    # print(book_value_prediction[-1])
    # print(liq_prediction[-1])
    # print(liq_NXM_b_prediction[-1])
    # print(liq_NXM_a_prediction[-1])

    # # RECORD STATE & MOVE TIME
    # print(datetime.fromtimestamp(block.timestamp))
    # print(datetime.fromtimestamp(block.timestamp) - datetime.now())

    # print(ramm.getSpotPriceB()/1e18)
    # print(ramm.getSpotPriceA()/1e18)

    # IMPERSONATING ACCOUNTS
