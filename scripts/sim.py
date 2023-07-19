from ape import networks, accounts, project
import click

def main():
    ecosystem_name = networks.provider.network.ecosystem.name
    network_name = networks.provider.network.name
    provider_name = networks.provider.name
    click.echo(f"You are connected to network '{ecosystem_name}:{network_name}:{provider_name}'.")

    click.echo(f"Deploying contracts")
    dev = accounts.test_accounts[0]
    dev.balance = int(1e27)

    nxm = dev.deploy(project.NXM)
    nxm.mint(dev, int(6_750_000 * 1e18), sender=dev)

    pool_eth = int(142_500 * 1e18)
    pool_dai = int(5_000_000 * 1e18)
    dai_rate = int(1e18) // 2000
    mcr = int(100_000 * 1e18)

    pool = dev.deploy(project.CapitalPool, pool_dai, dai_rate, mcr, value=pool_eth)
    ramm = dev.deploy(project.Ramm, nxm.address, pool.address)

    # DO A SWAP
    print(pool.getPoolValueInEth()/1e18)
    print(nxm.balanceOf(dev)/1e18)
    ramm.swap(0, value=int(1000e18), sender=dev)
    print(pool.getPoolValueInEth()/1e18)
    print(nxm.balanceOf(dev)/1e18)

    # MOVE TIME
    # block = networks.provider.get_block('latest')
    # print(block)
    # networks.provider.set_timestamp(block.timestamp + 3600)
    # networks.provider.mine()
    # print(networks.provider.get_block('latest'))

    # IMPERSONATING ACCOUNTS
