package sample

type BankAccount struct {
	Owner   string
	Balance float64
}

func NewBankAccount(owner string, balance float64) *BankAccount {
	return &BankAccount{Owner: owner, Balance: balance}
}

func (a *BankAccount) Deposit(amount float64) float64 {
	a.Balance += amount
	return a.Balance
}

func (a *BankAccount) Withdraw(amount float64) (float64, bool) {
	if amount > a.Balance {
		return a.Balance, false
	}
	a.Balance -= amount
	return a.Balance, true
}

func (a *BankAccount) GetBalance() float64 {
	return a.Balance
}

func Transfer(from, to *BankAccount, amount float64) bool {
	if amount > from.Balance {
		return false
	}
	from.Balance -= amount
	to.Balance += amount
	return true
}
