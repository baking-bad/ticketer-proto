from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.utility import (
    make_filename_from_build_name,
    to_michelson_type,
    to_micheline,
    pack,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from tests.helpers.tokens.token import TokenHelper
from typing import Any


class Ticketer(ContractHelper):
    # TODO: consider moving this to some consts file?
    TICKET_TYPE_EXPRESSION = 'pair (nat %token_id) (bytes %token_info)'

    default_storage = {
        'extra_metadata': {},
        'metadata': {},
        'token_ids': {},
        'tokens': {},
        'next_token_id': 0,
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Ticketer with empty storage"""

        filename = make_filename_from_build_name('ticketer')
        return cls.originate_from_file(filename, client, cls.default_storage)

    def deposit(self, token: TokenHelper, amount: int) -> ContractCall:
        params = (token.as_dict(), amount)
        return self.contract.deposit(params)

    def get_token_id(self, token: TokenHelper) -> int:
        token_ids = self.contract.storage['token_ids']
        token_id = token_ids[token.as_dict()]()  # type: ignore
        assert type(token_id) is int
        return token_id

    def make_ticket_transfer_params(
        self,
        token: TokenHelper,
        amount: int,
        destination: str,
        entrypoint: str
    ) -> dict[str, Any]:

        ticket_contents = {
            'token_id': self.get_token_id(token),
            'token_info': token.make_token_info_bytes()
        }

        return {
            'ticket_contents': to_michelson_type(
                    ticket_contents,
                    self.TICKET_TYPE_EXPRESSION,
                ).to_micheline_value(),
            'ticket_ty': to_micheline(self.TICKET_TYPE_EXPRESSION),
            'ticket_ticketer': self.address,
            'ticket_amount': amount,
            'destination': destination,
            'entrypoint': entrypoint,
        }
