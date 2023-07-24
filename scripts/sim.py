from ape import networks, accounts, project
import click
import numpy as np
from scripts.sys_params import pool_eth, pool_dai, dai_rate, mcr, nxm_supply

def main():
    ecosystem_name = networks.provider.network.ecosystem.name
    network_name = networks.provider.network.name
    provider_name = networks.provider.name
    click.echo(f"You are connected to network '{ecosystem_name}:{network_name}:{provider_name}'.")

    click.echo(f"Deploying contracts")
    dev = accounts.test_accounts[0]
    dev.balance = int(1e27)

    nxm = dev.deploy(project.NXM)
    nxm.mint(dev, nxm_supply, sender=dev)

    pool = dev.deploy(project.CapitalPool, pool_dai, dai_rate, mcr, value=pool_eth)
    ramm = dev.deploy(project.Ramm, nxm.address, pool.address)

    # Tracking Metrics
    cap_pool_prediction = np.array([pool.getPoolValueInEth()/1e18])
    price_b_prediction = np.array([ramm.getSpotPriceB()/1e18])
    price_a_prediction = np.array([ramm.getSpotPriceA()/1e18])
    nxm_supply_prediction = np.array([nxm.balanceOf(dev)/1e18])
    book_value_prediction = np.array([pool.getPoolValueInEth() / nxm.balanceOf(dev)])
    liq_prediction = np.array([ramm.getReserves()[0]/1e18])
    liq_NXM_b_prediction = np.array([ramm.getReserves()[2]/1e18])
    liq_NXM_a_prediction = np.array([ramm.getReserves()[1]/1e18])

    # DO A SWAP
    # print(pool.getPoolValueInEth()/1e18)
    # print(nxm.balanceOf(dev)/1e18)
    # ramm.swap(int(2000e18), sender=dev)
    print(cap_pool_prediction[-1])
    print(price_b_prediction[-1])
    print(price_a_prediction[-1])
    print(nxm_supply_prediction[-1])
    print(book_value_prediction[-1])
    print(liq_prediction[-1])
    print(liq_NXM_b_prediction[-1])
    print(liq_NXM_a_prediction[-1])
    # # RECORD STATE & MOVE TIME
    # block = networks.provider.get_block('latest')
    # print(block)
    # networks.provider.set_timestamp(block.timestamp + 3600)
    # networks.provider.mine()
    # print(networks.provider.get_block('latest'))

    # IMPERSONATING ACCOUNTS
