import smartpy as sp

class EventSink(sp.Contract):
    def __init__(self):
        self.init()

    #minting, transfer, burning events
    @sp.entry_point
    def transferEvent(self, params):
        sp.set_type(params, sp.TRecord(amount = sp.TIntOrNat, fromAddress = sp.TOption(sp.TAddress), toAddress = sp.TOption(sp.TAddress)))

    #approval events
    @sp.entry_point
    def approvalEvent(self, params):
        sp.set_type(params, sp.TRecord(amount = sp.TIntOrNat, owner = sp.TAddress, spender = sp.TAddress))

if "templates" not in __name__:
    @sp.add_test(name = "EventSink")
    def test():     


        scenario = sp.test_scenario()
        scenario.h1("EventSink for Ethereum like emit events")      

        alice = sp.test_account("Alice")
        bob   = sp.test_account("Robert")
        
        scenario.h1("Accounts")
        scenario.show([alice, bob])

        eventSink = EventSink()
        scenario += eventSink 

        scenario.h1("Mint")
        scenario += eventSink.transferEvent(amount = 4000000000000000000, fromAddress = sp.none, toAddress = sp.some(bob.address))
        scenario.h1("Burn")
        scenario += eventSink.transferEvent(amount = 4000000000000000000, fromAddress = sp.some(alice.address), toAddress = sp.none)
        scenario.h1("Transfer")
        scenario += eventSink.transferEvent(amount = 4000000000000000000, fromAddress = sp.some(alice.address), toAddress = sp.some(bob.address))
        scenario.h1("Approval")
        scenario += eventSink.approvalEvent(amount = 4000000000000000000, owner = alice.address, spender = bob.address)
