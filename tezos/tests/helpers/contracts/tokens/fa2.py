from os.path import join

from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup

from tezos.tests.helpers.contracts.tokens.token import TokenHelper
from tezos.tests.helpers.metadata import Metadata
from tezos.tests.helpers.utility import DEFAULT_ADDRESS
from tezos.tests.helpers.utility import get_tokens_dir
from tezos.tests.helpers.utility import originate_from_file
from tezos.tests.helpers.utility import pack
from tezos.tests.helpers.addressable import (
    Addressable,
    get_address,
)

FA2AsDictType = dict[str, tuple[str, int]]
FA2AsTupleType = tuple[str, tuple[str, int]]


class FA2(TokenHelper):
    default_storage = {
        'administrator': DEFAULT_ADDRESS,
        'all_tokens': 0,
        'issuer': DEFAULT_ADDRESS,
        'ledger': {},
        'metadata': Metadata.make(
            name='Test FA2 Token',
            description='Simple test FA2 token based on fxhash token from mainnet.',
        ),
        'operators': {},
        'paused': False,
        'signer': DEFAULT_ADDRESS,
        'token_data': {},
        'token_metadata': {},
        'treasury_address': DEFAULT_ADDRESS,
    }

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[Addressable, int], token_id: int = 0
    ) -> OperationGroup:
        """Deploys FA2 token with provided balances in the storage"""

        filename = join(get_tokens_dir(), 'fa2-fxhash.tz')
        storage = cls.default_storage.copy()
        storage['ledger'] = {
            (get_address(addressable), token_id): amount
            for addressable, amount in balances.items()
        }
        storage['token_metadata'] = {token_id: (token_id, {})}
        return originate_from_file(filename, client, storage)

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        return self.contract.update_operators(
            [
                {
                    'add_operator': {
                        'owner': get_address(owner),
                        'operator': get_address(operator),
                        'token_id': self.token_id,
                    }
                }
            ]
        )

    def disallow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        return self.contract.update_operators(
            [
                {
                    'remove_operator': {
                        'owner': get_address(owner),
                        'operator': get_address(operator),
                        'token_id': self.token_id,
                    }
                }
            ]
        )

    def as_dict(self) -> FA2AsDictType:
        return {'fa2': (self.address, self.token_id)}

    def as_tuple(self) -> FA2AsTupleType:
        return ('fa2', (self.address, self.token_id))

    def get_balance(self, client_or_contract: Addressable) -> int:
        address = get_address(client_or_contract)
        key = (address, self.token_id)
        balance = self.contract.storage['ledger'][key]()  # type: ignore
        assert isinstance(balance, int)
        return balance

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA2", 'string'),
            'token_id': pack(self.token_id, 'nat'),
        }
