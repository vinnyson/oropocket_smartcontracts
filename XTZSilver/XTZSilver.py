# Fungible Assets - FA12
# Inspired by https://gitlab.com/tzip/tzip/blob/master/A/FA1.2.md

import smartpy as sp

class FA12(sp.Contract):
    def __init__(self, admin, tokenName, symbol, decimals):
        self.init(paused = False, ledger = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)), administrator = admin, totalSupply = 0, name = tokenName, decimals = decimals, symbol = symbol)

    @sp.entry_point
    def transfer(self, params):
        sp.set_type(params, sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))))
        sp.verify((sp.sender == self.data.administrator) |
            (~self.data.paused &
                ((params.from_ == sp.sender) |
                 (self.data.ledger[params.from_].approvals[sp.sender] >= params.value))))
        self.addAddressIfNecessary(params.to_)
        sp.verify(self.data.ledger[params.from_].balance >= params.value)
        self.data.ledger[params.from_].balance = sp.as_nat(self.data.ledger[params.from_].balance - params.value)
        self.data.ledger[params.to_].balance += params.value
        #ownself and admin do not require approval amount
        sp.if (params.from_ != sp.sender) & (self.data.administrator != sp.sender):
            self.data.ledger[params.from_].approvals[sp.sender] = sp.as_nat(self.data.ledger[params.from_].approvals[sp.sender] - params.value)

    @sp.entry_point
    def approve(self, params):
        sp.set_type(params, sp.TRecord(spender = sp.TAddress, value = sp.TNat).layout(("spender", "value")))
        sp.verify(~self.data.paused)
        alreadyApproved = self.data.ledger[sp.sender].approvals.get(params.spender, 0)
        sp.verify((alreadyApproved == 0) | (params.value == 0), "UnsafeAllowanceChange")
        self.data.ledger[sp.sender].approvals[params.spender] = params.value

    @sp.entry_point
    def setPause(self, params):
        sp.set_type(params, sp.TBool)
        sp.verify(sp.sender == self.data.administrator)
        self.data.paused = params

    @sp.entry_point
    def setAdministrator(self, params):
        sp.set_type(params, sp.TAddress)
        sp.verify(sp.sender == self.data.administrator)
        self.data.administrator = params

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(sp.sender == self.data.administrator)
        self.addAddressIfNecessary(params.address)
        self.data.ledger[params.address].balance += params.value
        self.data.totalSupply += params.value


    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(self.data.ledger[params.address].balance >= params.value)
        self.data.ledger[params.address].balance = sp.as_nat(self.data.ledger[params.address].balance - params.value)
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)

    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.ledger.contains(address):
            self.data.ledger[address] = sp.record(balance = 0, approvals = {})

    @sp.view(sp.TNat)		
    def getBalance(self, params):		
        sp.result(self.data.ledger[params].balance)	
        	
    @sp.view(sp.TNat)		
    def getAllowance(self, params):		
        sp.result(self.data.ledger[params.owner].approvals[params.spender])	
        		
    @sp.view(sp.TNat)		
    def getTotalSupply(self, params):		
        sp.set_type(params, sp.TUnit)		
        sp.result(self.data.totalSupply)	
        		
    @sp.view(sp.TAddress)		
    def getAdministrator(self, params):		
        sp.set_type(params, sp.TUnit)		
        sp.result(self.data.administrator)
        

class Viewer(sp.Contract):
    def __init__(self, t):
        self.init(last = sp.none)
        self.init_type(sp.TRecord(last = sp.TOption(t)))
    @sp.entry_point
    def target(self, params):
        self.data.last = sp.some(params)

if "templates" not in __name__:
    @sp.add_test(name = "FA12")
    def test():

        scenario = sp.test_scenario()
        scenario.h1("FA1.2 template - Fungible assets")

        scenario.table_of_contents()

        # sp.test_account generates ED25519 key-pairs deterministically:
        admin = sp.test_account("Administrator")
        alice = sp.test_account("Alice")
        bob   = sp.test_account("Robert")

        # Let's display the accounts:
        scenario.h1("Accounts")
        scenario.show([admin, alice, bob])

        scenario.h1("Contract")
        c1 = FA12(admin.address, tokenName = "OroPocket Silver", symbol = "XTZSilver", decimals = 6)

        scenario.h1("Entry points")
        scenario += c1
        #add number of zeros in place of decimals as Michelson does not support decimals
        #000000000000000000
        scenario.h2("Admin mints a few coins")
        scenario += c1.mint(address = alice.address, value = 12000000000000000000).run(sender = admin)
        scenario += c1.mint(address = alice.address, value = 3000000000000000000).run(sender = admin)
        scenario += c1.mint(address = alice.address, value = 3000000000000000000).run(sender = admin)
        scenario.h2("Alice transfers to Bob")
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4000000000000000000).run(sender = alice)
        scenario.verify(c1.data.ledger[alice.address].balance == 14000000000000000000)
        scenario.h2("Bob tries to transfer from Alice but he doesn't have her approval")
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4000000000000000000).run(sender = bob, valid = False)
        scenario.h2("Alice approves Bob and Bob transfers")
        scenario += c1.approve(spender = bob.address, value = 5000000000000000000).run(sender = alice)
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4000000000000000000).run(sender = bob)
        scenario.h2("Bob tries to over-transfer from Alice")
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4000000000000000000).run(sender = bob, valid = False)
        scenario.h2("Admin burns Bob token")
        scenario += c1.burn(address = bob.address, value = 1000000000000000000).run(sender = admin)
        scenario.verify(c1.data.ledger[alice.address].balance == 10000000000000000000)
        scenario.h2("Alice tries to burn Bob token")
        scenario += c1.burn(address = bob.address, value = 1000000000000000000).run(sender = alice, valid = False)
        scenario.h2("Admin pauses the contract and Alice cannot transfer anymore")
        scenario += c1.setPause(True).run(sender = admin)
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4000000000000000000).run(sender = alice, valid = False)
        scenario.verify(c1.data.ledger[alice.address].balance == 10000000000000000000)
        scenario.h2("Admin transfers while on pause")
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1000000000000000000).run(sender = admin)
        scenario.h2("Admin unpauses the contract and transferts are allowed")
        scenario += c1.setPause(False).run(sender = admin)
        scenario.verify(c1.data.ledger[alice.address].balance == 9000000000000000000)
        scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1000000000000000000).run(sender = alice)
        scenario.verify(c1.data.totalSupply == 17000000000000000000)
        scenario.verify(c1.data.ledger[alice.address].balance == 8000000000000000000)
        scenario.verify(c1.data.ledger[bob.address].balance == 9000000000000000000)

        scenario.h1("Views")
        scenario.h2("Balance")
        view_balance = Viewer(sp.TNat)
        scenario += view_balance
        scenario += c1.getBalance((alice.address, view_balance.address))
        scenario.verify_equal(view_balance.data.last, sp.some(8000000000000000000))

        scenario.h2("Administrator")
        view_administrator = Viewer(sp.TAddress)
        scenario += view_administrator
        scenario += c1.getAdministrator((sp.unit, view_administrator.address))
        scenario.verify_equal(view_administrator.data.last, sp.some(admin.address))

        scenario.h2("Total Supply")
        view_totalSupply = Viewer(sp.TNat)
        scenario += view_totalSupply
        scenario += c1.getTotalSupply((sp.unit, view_totalSupply.address))
        scenario.verify_equal(view_totalSupply.data.last, sp.some(17000000000000000000))

        scenario.h2("Allowance")
        view_allowance = Viewer(sp.TNat)
        scenario += view_allowance
        scenario += c1.getAllowance((sp.record(owner = alice.address, spender = bob.address), view_allowance.address))
        scenario.verify_equal(view_allowance.data.last, sp.some(1000000000000000000))