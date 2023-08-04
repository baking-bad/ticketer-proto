#import "./common/tokens/index.mligo" "Token"
#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


module Ticketer = struct

    type storage = {
        extra_metadata : (Token.t, Types.token_info) map;
        metadata : (string, bytes) big_map;
        // TODO: decide, should we keep this ids registry or this is not required?
        token_ids : (Token.t, nat) big_map;
        tokens : (nat, Token.t) big_map;
        next_token_id : nat;
    }

    type return = operation list * storage

    let add_token (token : Token.t) (store : storage) : storage = {
            store with
            token_ids = Big_map.add token store.next_token_id store.token_ids;
            tokens = Big_map.add store.next_token_id token store.tokens;
            next_token_id = store.next_token_id + 1n;
        }

    [@entry] let deposit (token, amount : Token.t * nat) (store : storage) : return =
        // TODO: decide: should we limit Token.contract_address that allowed to be
        //       converted to ticket? (it is easier to start with the most general
        //       case, so the answer is "no" for now)
        let new_store, token_id : storage * nat =
            match Big_map.find_opt token store.token_ids with
            | None -> (add_token token store, store.next_token_id)
            | Some id -> (store, id) in
        let payload = {
            token_id = token_id;
            // TODO: add extra_metadata if there is any info about token
            token_info = Some (Bytes.pack (Token.make_token_info token));
        } in
        let sr_ticket = Utility.create_ticket (payload, amount) in
        let sender = Tezos.get_sender () in
        let sender_contract = Utility.get_ticket_entrypoint (sender) in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op token amount sender self in
        let ticket_transfer_op = Tezos.transaction sr_ticket 0mutez sender_contract in
        [token_transfer_op; ticket_transfer_op], new_store

    [@entry] let release (sr_ticket, destination : (Types.payload ticket) * address) (store : storage) : return =
        let (ticketer, (payload, amount)), _ = Tezos.read_ticket sr_ticket in
        let _ = Utility.assert_address_is_self ticketer in
        let token =
            match Big_map.find_opt payload.token_id store.tokens with
            | None -> failwith Errors.token_not_found
            | Some t -> t in
        let self = Tezos.get_self_address () in
        let transfer_op = Token.get_transfer_op token amount self destination in
        [transfer_op], store
end
