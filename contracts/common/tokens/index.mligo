#import "./fa2.mligo" "TokenFa2"
#import "./fa12.mligo" "TokenFa12"
#import "../types.mligo" "Types"

type t =
    | Fa12 of TokenFa12.t
    | Fa2 of TokenFa2.t

// TODO: check this code that generated by copilot:
let get_transfer_op (token: t) (amount: nat) (from_: address) (to_: address) : operation =
    match token with
    | Fa12 addr -> TokenFa12.get_transfer_op from_ to_ addr amount
    | Fa2 (addr, token_id) -> begin
        let txs = [ { to_ = to_; token_id = token_id; amount = amount; } ] in
        TokenFa2.get_transfer_op from_ addr txs
    end

let make_token_info (token : t) : Types.token_info =
    match token with
    | Fa12 addr -> Map.literal [
        ("contract_address", Bytes.pack addr);
        ("token_type", Bytes.pack "FA1.2");
    ]
    | Fa2 (addr, token_id) -> Map.literal [
        ("contract_address", Bytes.pack addr);
        ("token_id", Bytes.pack token_id);
        ("token_type", Bytes.pack "FA2");
    ]
