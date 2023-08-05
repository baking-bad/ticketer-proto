(* Context is set by implicit address before ticket send:
    - data is the data that will be added to the ticket
    - receiver is the address of the contract that will receive the ticket
*)
// TODO: consider clearing context after each send
// TODO: consider adding some id to simplify external indexing

// TODO: context structure should be different, in one case this is receiver,
// in other this is routing_data, sol looks like context itself should be generic
type 'data context_t = {
    data : 'data;
    receiver : address;
}

// TODO: is it required to have empty context? (and reset it after each send?)
// Storage implements per-user context for increased security:
type 'data t = (address, 'data context_t) big_map