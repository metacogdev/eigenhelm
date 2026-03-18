struct BankAccount {
    owner: String,
    balance: f64,
}

impl BankAccount {
    fn new(owner: &str, balance: f64) -> BankAccount {
        BankAccount {
            owner: String::from(owner),
            balance,
        }
    }

    fn deposit(&mut self, amount: f64) -> f64 {
        self.balance += amount;
        self.balance
    }

    fn withdraw(&mut self, amount: f64) -> Option<f64> {
        if amount > self.balance {
            None
        } else {
            self.balance -= amount;
            Some(self.balance)
        }
    }

    fn get_balance(&self) -> f64 {
        self.balance
    }

    fn get_owner(&self) -> &str {
        &self.owner
    }
}
