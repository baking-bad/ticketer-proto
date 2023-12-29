import click
import subprocess
from typing import Optional
from scripts.environment import load_or_ask
from tezos.tests.helpers.utility import make_address_bytes


@click.command()
@click.option('--public-key', default=None, help='Etherlink address to fund.')
@click.option(
    '--sender-private-key',
    default=None,
    help='Use the provided private key to fund from.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def fund_account(
    public_key: Optional[str],
    sender_private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Funds given Etherlink address with 1 tez"""

    public_key = public_key or load_or_ask('L2_PUBLIC_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    sender_private_key = sender_private_key or load_or_ask('L2_MASTER_KEY')

    result = subprocess.run(
        [
            'cast',
            'send',
            public_key,
            '--value',
            '1ether',
            '--private-key',
            sender_private_key,
            '--rpc-url',
            rpc_url,
            '--legacy',
        ],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )
    print('Successfully funded account:')
    print(result.stdout)


@click.command()
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticketer-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
# TODO: consider extracting token name from the ticketer content bytes
@click.option(
    '--token-name', required=True, help='The name of the ERC20 token on Etherlink side.'
)
@click.option(
    '--token-symbol',
    required=True,
    help='The symbol of the ERC20 token on Etherlink side.',
)
@click.option(
    '--decimals',
    default=0,
    help='The number of decimals of the ERC20 token on Etherlink side.',
)
@click.option(
    '--kernel-address',
    default=None,
    help='The address of the Etherlink kernel which will be managing token.',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def deploy_erc20(
    ticketer_address_bytes: str,
    ticketer_content_bytes: str,
    token_name: str,
    token_symbol: str,
    decimals: int,
    kernel_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Deploys ERC20 Proxy contract with given parameters"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    result = subprocess.run(
        [
            'forge',
            'create',
            '--legacy',
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            'src/ERC20Proxy.sol:ERC20Proxy',
            '--constructor-args',
            ticketer_address_bytes,
            ticketer_content_bytes,
            kernel_address,
            token_name,
            token_symbol,
            '0',
            '--gas-limit',
            '200000',
        ],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )

    print('Successfully deployed ERC20 contract:')
    print(result.stdout)


@click.command()
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20 proxy token contract which should burn token.',
)
@click.option(
    '--router-address',
    required=True,
    help='The address of the Router contract on the Tezos side (Ticketer address for FA2 and FA1.2 tokens).',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be withdrawn.'
)
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticketer-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--receiver-address',
    default=None,
    help='The address of the receiver of the tokens in Tezos.',
)
@click.option(
    '--withdraw-precompile',
    default=None,
    help='The address of the withdraw precompile contract.',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def withdraw(
    proxy_address: str,
    router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticketer_content_bytes: str,
    receiver_address: Optional[str],
    withdraw_precompile: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Withdraws token from L2 to L1"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    withdraw_precompile = withdraw_precompile or load_or_ask(
        'L2_WITHDRAW_PRECOMPILE_ADDRESS'
    )

    receiver_address = receiver_address or load_or_ask('L1_PUBLIC_KEY_HASH')
    receiver_address_bytes = make_address_bytes(receiver_address)
    routing_info = receiver_address_bytes + ticketer_address_bytes

    result = subprocess.run(
        [
            'cast',
            'send',
            withdraw_precompile,
            'withdraw(address,bytes,uint256,bytes22,bytes)',
            proxy_address,
            routing_info,
            str(amount),
            ticketer_address_bytes,
            ticketer_content_bytes,
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            '--legacy',
            '--gas-limit',
            '300000',
        ],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )

    print('Successfully called withdraw:')
    print(result.stdout)
