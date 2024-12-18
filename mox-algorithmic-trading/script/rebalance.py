from script._setup_script import setup_script
import boa
from moccasin.config import get_active_network, get_config, _Networks
from boa.contracts.abi.abi_contract import ABIContract


TARGET_ALLOCATIONS = {"usdc": 0.3, "weth": 0.7}
BUFFER = 0.1
SIX_DECIMALS = 1_000_000
EIGHTEEN_DECIMALS = 1_000_000_000_000_000_000


def calculate_rebalancing_trades(
    usdc_data: dict,
    weth_data: dict,
    target_allocations: dict[str, float]) -> dict[str, dict]:

    # Calculate current values
    usdc_value = usdc_data["balance"] * usdc_data["price"]
    weth_value = weth_data["balance"] * weth_data["price"]
    total_value = usdc_value + weth_value

    # Calculate target values
    target_usdc_value = total_value * target_allocations["usdc"]
    target_weth_value = total_value * target_allocations["weth"]

    # Calculate trades needed in USD
    usdc_trade_usd = target_usdc_value - usdc_value
    weth_trade_usd = target_weth_value - weth_value

    # Convert to token amounts
    return {
        "usdc": {
            "contract": usdc_data["contract"],
            "trade": usdc_trade_usd / usdc_data["price"],
        },
        "weth": {
            "contract": weth_data["contract"],
            "trade": weth_trade_usd / weth_data["price"],
        },
    }


def print_token_balance(usdc, weth, a_usdc, a_weth):
    print(f'USDC balance: {usdc.balanceOf(boa.env.eoa)}')
    print(f'WETH balance: {weth.balanceOf(boa.env.eoa)}')
    print(f'aUSDC balance: {a_usdc.balanceOf(boa.env.eoa)}')
    print(f'aWETH balance: {a_weth.balanceOf(boa.env.eoa)}')


def get_price(feed_name: str) -> float:
    active_network = get_active_network()
    price_feed = active_network.manifest_named(feed_name)
    price = price_feed.latestAnswer() 
    decimals = price_feed.decimals()
    decimals_normalized = 10 ** decimals
    return price / decimals_normalized


def rebalance(usdc: ABIContract, weth: ABIContract, a_usdc: ABIContract, a_weth: ABIContract):
    a_usdc_balance = a_usdc.balanceOf(boa.env.eoa)
    a_weth_balance = a_weth.balanceOf(boa.env.eoa)

    a_usdc_balance_normalized = a_usdc_balance / SIX_DECIMALS
    a_weth_balance_normalized = a_weth_balance / EIGHTEEN_DECIMALS

    usdc_value = a_usdc_balance_normalized * get_price('usdc_usd')
    weth_value = a_weth_balance_normalized * get_price('eth_usd')

    total_value = usdc_value + weth_value
    usdc_percent_allocation = usdc_value / total_value
    weth_percent_allocation = weth_value / total_value

    print(f"Current percent allocation of USDC: {usdc_value / total_value * 100:.2f}%")
    print(f"Current percent allocation of WETH: {weth_value / total_value * 100:.2f}%")

    needs_rebalance = (
        abs(usdc_percent_allocation - TARGET_ALLOCATIONS['usdc']) > BUFFER
        or abs(weth_percent_allocation - TARGET_ALLOCATIONS['weth']) > BUFFER
    )

    if needs_rebalance:
        print("Rebalancing needed!")
        print(f"Target allocation of USDC: {TARGET_ALLOCATIONS['usdc'] * 100:.2f}%")
        print(f"Target allocation of WETH: {TARGET_ALLOCATIONS['weth'] * 100:.2f}%")

        trades_tokens = calculate_rebalancing_trades(
            {
                "balance": a_usdc_balance_normalized,
                "price": get_price('usdc_usd'),
                "contract": usdc,
            },
            {
                "balance": a_weth_balance_normalized,
                "price": get_price("eth_usd"),
                "contract": weth,
            },
            TARGET_ALLOCATIONS,
        )

        trades_tokens["usdc"]["a_token"] = a_usdc
        trades_tokens["weth"]["a_token"] = a_weth

        print(trades_tokens)

        active_network = get_active_network()
        aavev3_pool_address_provider = active_network.manifest_named('aavev3_pool_address_provider')
        pool_address: str = aavev3_pool_address_provider.getPool()
        pool_contract = active_network.manifest_named('aavev3_pool', address=pool_address)

        trades_token_to_buy = (
            trades_tokens["usdc"] if trades_tokens["usdc"]["trade"] > 0 else trades_tokens["weth"]
        )

        trades_token_to_sell = (
            trades_tokens["usdc"] if trades_tokens["usdc"]["trade"] < 0 else trades_tokens["weth"]
        )

        amount_in = abs(int(trades_token_to_sell["trade"] * (10 ** trades_token_to_sell["contract"].decimals())))
        amount_out = int(trades_token_to_buy["trade"] * (10 ** trades_token_to_buy["contract"].decimals()) * 0.95)

        trades_token_to_sell["a_token"].approve(pool_contract.address, amount_in)
        withdraw_amount = trades_token_to_sell["a_token"].balanceOf(boa.env.eoa)
        pool_contract.withdraw(trades_token_to_sell["contract"].address, withdraw_amount, boa.env.eoa)

        uniswap_swap_router = active_network.manifest_named("uniswap_swap_router")
        trades_token_to_sell["contract"].approve(uniswap_swap_router.address, amount_in)

        print(f"Time to swap amount_in: {amount_in}!")
        print(
            f"Let's swap {amount_in / (10 ** trades_token_to_sell["contract"].decimals())} {trades_token_to_sell["contract"].symbol()} for at least {amount_out / (10 ** trades_token_to_buy["contract"].decimals())} {trades_token_to_buy["contract"].symbol()}"
        )

        amount_out = swap_exact_input_single(
            swap_router=uniswap_swap_router,
            token_in_contract=trades_token_to_sell["contract"],
            token_out_contract=trades_token_to_buy["contract"],
            amount_in=amount_in,
            amount_out_min=amount_out,
        )


def swap_exact_input_single(
    swap_router,
    token_in_contract,
    token_out_contract,
    amount_in: int,
    amount_out_min: int,
    pool_fee: int = 3000) -> int:

    token_in_contract.approve(swap_router.address, amount_in)

    amount_out = swap_router.exactInputSingle(
        (
            token_in_contract.address,
            token_out_contract.address,
            pool_fee,
            boa.env.eoa,
            int(amount_in),
            int(amount_out_min),
            0,
        )
    )

    return amount_out


def moccasin_main():
    usdc, weth, a_usdc, a_weth = setup_script()
    rebalance(usdc, weth, a_usdc, a_weth)