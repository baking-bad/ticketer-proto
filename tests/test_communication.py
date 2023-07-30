from tests.base import BaseTestCase
from tests.helpers.routing_data import create_routing_data
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
    create_expected_ticket,
)


# Packed payload for the ticket created in the test below:
PACKED_PAYLOAD = '05020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a0000001601d7c501ea0ec67b512caf24564077c1dceb105ac20007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a00000009050100000003464132'


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # Bridging FA2 / FA1.2 token includes next steps:
        # 1. Allow ticketer to transfer tokens
        # 2. Make ticket from tokens by depositing them to the ticketer
        # 3. Transfer tickets to the Rollup (which is represeented by Locker)
        #    - as far as implicit address can't send tickets with extra data
        #      we use special proxy contract to do this

        # First we check that ticketer has no tickets and no tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 0
        assert len(self.rollup_mock.get_tickets()) == 0

        # Then we configure ticket transfer params and routing info:
        ticket_params = self.ticketer.make_ticket_transfer_params(
            token=self.fa2,
            amount=25,
            destination=self.proxy.address,
            entrypoint='send_ticket',
        )

        # Here we create routing data for the proxy contract that will
        # create "L2" ticket in the Rollup contract for Alice:
        routing_data = create_routing_data(
            refund_address=pkh(self.alice),
            l2_address=pkh(self.alice),
        )

        # Then in one bulk we allow ticketer to transfer tokens,
        # deposit tokens to the ticketer, set routing info to the proxy
        # and transfer ticket to the Rollup (Locker) by sending created ticket
        # to the proxy contract, which will send it to the Rollup with routing info:
        self.alice.bulk(
            self.fa2.using(self.alice).allow(self.ticketer.address),
            self.ticketer.using(self.alice).deposit(self.fa2, 100),
            self.proxy.using(self.alice).set({
                'data': routing_data,
                'receiver': self.rollup_mock.address,
            }),
            self.alice.transfer_ticket(**ticket_params),
        ).send()

        self.bake_block()

        # Checking operations results:
        # 1. Rollup has L1 tickets:
        expected_l1_ticket = create_expected_ticket(
            ticketer=self.ticketer.address,
            token_id=0,
            payload=PACKED_PAYLOAD,
        )
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            self.rollup_mock.address,
        )
        self.assertEqual(balance, 25)

        # 2. Ticketer has FA2 tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 100

        # 3. Alice has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            pkh(self.alice),
        )
        self.assertEqual(balance, 75)

        # 4. Alice has L2 tickets:
        expected_l2_ticket = create_expected_ticket(
            ticketer=self.rollup_mock.address,
            token_id=0,
            payload=PACKED_PAYLOAD,
        )
        balance = get_ticket_balance(
            self.client,
            expected_l2_ticket,
            pkh(self.alice),
        )
        self.assertEqual(balance, 25)

        # Transfer some L2 tickets to another address
        # TODO: burn some L2 tickets to get L1 tickets back on another address
        # TODO: unpack L1 tickets to get back FA2 tokens

    # TODO: test_should_return_ticket_to_sender_if_wrong_payload
    # TODO: test_minted_ticket_should_have_expected_content_and_type

    # TODO: ? multiple users add same tickets to rollup mock
    # TODO: ? different tickets from one ticketer
