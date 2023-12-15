from tests.base import BaseTestCase
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
)


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        boris = self.accs['boris']
        alice = self.accs['alice']
        fa2 = self.contracts['fa2']
        rollup_mock = self.contracts['rollup_mock']
        ticketer = self.contracts['ticketer']
        router = self.contracts['router']
        ticket_helper = self.contracts['ticket_helper']

        ticket = ticketer.get_ticket()

        # There are two addresses on L2, the first one is ERC20 proxy contract,
        # which would receve L2 tickets and the second is the Alice L2 address,
        # which would receive L2 tokens minted by ERC20 proxy contract:
        token_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - ticketer allowed to transfer tokens from Alice,
        # - Alice calls deposit tokens to the ticketer,
        # - Alice set routing info to the proxy
        #   (as far as implicit address can't send tickets with extra data),
        # - Alice transfer ticket to the Rollup via proxy contract.
        routing_info = token_proxy + alice_l2_address
        rollup = f'{rollup_mock.address}%rollup'
        alice.bulk(
            fa2.using(alice).allow(ticket_helper.address),
            ticket_helper.using(alice).deposit(rollup, routing_info, 100),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        # - Rollup has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            rollup_mock.address,
        )
        self.assertEqual(balance, 100)

        # - Ticketer has FA2 tokens:
        assert fa2.get_balance(ticketer.address) == 100

        # - Alice has no L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(alice),
        )
        self.assertEqual(balance, 0)

        # Then some interactions on L2 leads to outbox message creation:
        # for example Alice send some L2 tokens to Boris and Boris decided
        # to bridge 5 of them back to L1.
        rollup_mock.using(boris).create_outbox_message(
            {
                'ticket_id': {
                    'ticketer': ticket['ticketer'],
                    'token_id': 0,
                },
                'amount': 5,
                'routing_data': pack(pkh(boris), 'address'),
                'router': ticketer.address,
            }
        ).send()
        self.bake_block()

        # To withdraw tokens from the rollup, someone should execute outbox
        # message, which would call ticketer contract to burn tickets and
        # transfer tokens to the Boris address:
        boris_tokens_before_burn = fa2.get_balance(pkh(boris))
        rollup_mock.execute_outbox_message(0).send()
        self.bake_block()

        # Checking withdraw operations results:
        # - Rollup should have 95 L1 tickets left:
        balance = get_ticket_balance(
            self.client,
            ticket,
            rollup_mock.address,
        )
        self.assertEqual(balance, 95)

        # - Boris should have more FA2 tokens now:
        boris_tokens_after_burn = fa2.get_balance(pkh(boris))
        self.assertEqual(boris_tokens_after_burn, boris_tokens_before_burn + 5)
