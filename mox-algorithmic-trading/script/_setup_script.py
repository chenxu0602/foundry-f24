import boa
from boa.contracts.abi.abi_contract import ABIContract
from moccasin.config import get_active_network, Network


STARTING_ETH_BALANCE = int(1000e18)
STARTING_WETH_BALANCE = int(1e18)
STARTING_USDC_BALANCE = int(100e6)

def _add_eth_balance():
    boa.env.set_balance(boa.env.eoa, STARTING_ETH_BALANCE)


def _add_token_balance(usdc: ABIContract, weth: ABIContract):
    print(f'Starting balance of WETH: {weth.balanceOf(boa.env.eoa)}')
    weth.deposit(value=STARTING_WETH_BALANCE)
    print(f'Ending balance of WETH: {weth.balanceOf(boa.env.eoa)}')

    print(f'USDC balance before: {usdc.balanceOf(boa.env.eoa)}')
    our_address = boa.env.eoa
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(our_address)

    usdc.configureMinter(our_address, STARTING_USDC_BALANCE)
    usdc.mint(our_address, STARTING_USDC_BALANCE)
    print(f'USDC balance after: {usdc.balanceOf(boa.env.eoa)}')


def setup_script() -> tuple[ABIContract, ABIContract, ABIContract, ABIContract]:
    print('Starting setup script ...')

    active_network = get_active_network()

    usdc = active_network.manifest_named('usdc')
    weth = active_network.manifest_named('weth')
    aavev3_pool_address_provider = active_network.manifest_named('aavev3_pool_address_provider')
    pool_address = aavev3_pool_address_provider.getPool()
    print(pool_address)
    aavev3_pool_contract = active_network.manifest_named('aavev3_pool', address=pool_address)

    if active_network.is_local_or_forked_network():
        _add_eth_balance()
        _add_token_balance(usdc, weth)

    print('Getting atokens ...')
    aave_protocol_data_provider = active_network.manifest_named('aave_protocol_data_provider')
    a_tokens = aave_protocol_data_provider.getAllATokens()
    a_weth = None
    a_usdc = None

    for a_token in a_tokens:
        if 'WETH' in a_token[0]:
            a_weth = active_network.manifest_named('weth', address=a_token[1])
        if 'USDC' in a_token[0]:
            a_usdc = active_network.manifest_named('usdc', address=a_token[1])

    print(a_weth)
    print(a_usdc)

    starting_usdc_balance = usdc.balanceOf(boa.env.eoa)
    starting_weth_balance = weth.balanceOf(boa.env.eoa)

    a_usdc_balance = a_usdc.balanceOf(boa.env.eoa)
    a_weth_balance = a_weth.balanceOf(boa.env.eoa)

    print(f"Starting WETH balance: {starting_weth_balance}")
    print(f"Starting USDC balance: {starting_usdc_balance}")
    print(f"Starting aWETH balance: {a_weth_balance}")
    print(f"Starting aUSDC balance: {a_usdc_balance}")

    a_weth_balance_normalized = a_weth_balance / 1e18
    a_usdc_balance_normalized = a_usdc_balance / 1e6

    print(f'Normalized aWETH balance: {a_weth_balance_normalized}')
    print(f'Normalized aUSDC balance: {a_usdc_balance_normalized}')

    return usdc, weth, a_usdc, a_weth


def moccasin_main():
    setup_script()