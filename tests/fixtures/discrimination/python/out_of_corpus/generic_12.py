class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            return None
        self.balance -= amount
        return self.balance

    def get_balance(self):
        return self.balance

    def transfer(self, other, amount):
        if amount > self.balance:
            return False
        self.balance -= amount
        other.balance += amount
        return True
