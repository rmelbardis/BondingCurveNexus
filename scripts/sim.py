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

    pool_eth = int(142_500 * 1e18)
    pool_dai = int(5_000_000 * 1e18)
    dai_rate = int(1e18) // 2000
    mcr = int(100_000 * 1e18)

    pool = dev.deploy(project.CapitalPool, pool_dai, dai_rate, mcr, value=pool_eth)
    ramm = dev.deploy(project.Ramm, nxm.address, pool.address)
