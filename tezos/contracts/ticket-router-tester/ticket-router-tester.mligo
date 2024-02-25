#import "../common/types/routing-info.mligo" "RoutingInfo"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/types/ticket.mligo" "Ticket"


module TicketRouterTester = struct
    (*
        TicketRouterTester is a helper contract that helps developers test
        Etherlink Bridge ticket layer protocol components. It provides
        a simple interface to mint, deposit and withdraw tickets to and from
        Etherlink Bridge.

        There is the `set` entrypoint which allows to configure how tickets
        will be handled after `mint`, `default` and `withdraw` calls. Three
        options are available:
        - `default` which allows to redirect/mint ticket to the
            implicit address
        - `routerWithdraw` which allows to redirect/mint ticket to the ticketer
            `withdraw` entrypoint
        - `rollupDeposit` which allows to redirect/mint ticket to the
            rollup `deposit` entrypoint

        Also, two entrypoints allow TicketRouterTester to receive tickets
        from other contracts:
        - `default` accepts tickets in the same way implicit address would do
        - `withdraw` accepts tickets and redirects in the same way
           ticketer would do

        Finally, there is a `mint` entrypoint allowing to mint tickets and
        then redirect them to the configured entrypoint.

        This contract is expected to be used only for testing purposes.
    *)

    type entrypoint_t =
        | Default of unit
        | RouterWithdraw of address
        | RollupDeposit of RoutingInfo.l1_to_l2_t

    type internal_call_t = [@layout:comb] {
        target : address;
        entrypoint : entrypoint_t;
        xtz_amount : tez;
    }

    type storage_t = [@layout:comb] {
        internal_call : internal_call_t;
        metadata : (string, bytes) big_map;
    }

    type mint_params_t = [@layout:comb] {
        content : Ticket.content_t;
        amount : nat;
    }

    type return_t = operation list * storage_t

    [@entry] let set
            (internal_call : internal_call_t)
            (store : storage_t) : return_t =
        [], { store with internal_call }

    let make_operation
            (ticket : Ticket.t)
            (store : storage_t) : operation =
        let { target; entrypoint; xtz_amount } = store.internal_call in
        match entrypoint with
        | Default () ->
            let entry = Ticket.get_ticket_entrypoint target in
            Tezos.transaction ticket xtz_amount entry
        | RouterWithdraw (receiver) ->
            let withdraw = { receiver; ticket } in
            let entry = RouterWithdrawEntry.get target in
            Tezos.transaction withdraw xtz_amount entry
        | RollupDeposit (routing_info) ->
            let deposit = { routing_info; ticket } in
            let deposit_wrap = RollupDepositEntry.wrap deposit in
            let entry = RollupDepositEntry.get target in
            Tezos.transaction deposit_wrap xtz_amount entry

    [@entry] let default
            (ticket : Ticket.t)
            (store : storage_t) : return_t =
        [make_operation ticket store], store

    [@entry] let withdraw
            (params : RouterWithdrawEntry.t)
            (store : storage_t) : return_t =
        // NOTE: the receiver from params is dropped and used
        // the one from the store.internal_call
        [make_operation params.ticket store], store

    [@entry] let mint
            (params : mint_params_t)
            (store : storage_t) : return_t =
        let { content; amount } = params in
        let ticket = Ticket.create content amount in
        [make_operation ticket store], store
end
