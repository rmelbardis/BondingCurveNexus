from ape import networks, accounts, project
import click
import numpy as np
from datetime import datetime
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
    price_b_prediction = np.array([ramm.getSpotPriceB()/1e18])
    price_a_prediction = np.array([ramm.getSpotPriceA()/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])

    block = networks.provider.get_block('latest')
    times = np.array([block.timestamp])

    # DO A SWAP
    # print(datetime.fromtimestamp(times[-1]))
    # print(datetime.now())
    # print(datetime.fromtimestamp(times[-1]) - datetime.now())
    # ramm.swap(int(2000e18), sender=dev)
    print(book_value_prediction[-1])
    print(f'price pre-swap: {price_b_prediction[0]}')
    ramm.swap(int(3333.333 * 1e18), sender=dev)
    price_b_prediction = np.append(price_b_prediction, [ramm.getSpotPriceB()/1e18])
    print(f'price post-swap: {price_b_prediction[1]}')
    print(f'price impact - {100 * (price_b_prediction[1] - price_b_prediction[0]) / price_b_prediction[0]}%')
    # print(book_value_prediction[-1])
    # print(liq_prediction[-1])
    # print(liq_NXM_b_prediction[-1])
    # print(liq_NXM_a_prediction[-1])

    # # RECORD STATE & MOVE TIME
    # block = networks.provider.get_block('latest')
    # print(block)
    # networks.provider.set_timestamp(block.timestamp + 3600)
    # networks.provider.mine()
    # block = networks.provider.get_block('latest')
    # print(datetime.fromtimestamp(block.timestamp))
    # print(datetime.fromtimestamp(block.timestamp) - datetime.now())

    # print(ramm.getSpotPriceB()/1e18)
    # print(ramm.getSpotPriceA()/1e18)
    # IMPERSONATING ACCOUNTS
