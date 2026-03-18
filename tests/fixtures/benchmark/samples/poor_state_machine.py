class OrderProcessor:
    """Process orders through states. Boolean flags instead of proper state machine."""

    def __init__(self):
        self.is_new = True
        self.is_validated = False
        self.is_paid = False
        self.is_shipped = False
        self.is_delivered = False
        self.is_cancelled = False
        self.is_refunded = False
        self.items = []
        self.total = 0
        self.errors = []

    def validate(self):
        if self.is_new and not self.is_cancelled:
            if len(self.items) > 0:
                if self.total > 0:
                    self.is_validated = True
                    self.is_new = False
                    return True
                else:
                    self.errors.append("zero total")
                    return False
            else:
                self.errors.append("no items")
                return False
        else:
            self.errors.append("cannot validate")
            return False

    def pay(self):
        if self.is_validated and not self.is_paid and not self.is_cancelled:
            self.is_paid = True
            return True
        else:
            self.errors.append("cannot pay")
            return False

    def ship(self):
        if self.is_paid and not self.is_shipped and not self.is_cancelled:
            self.is_shipped = True
            return True
        else:
            self.errors.append("cannot ship")
            return False

    def deliver(self):
        if self.is_shipped and not self.is_delivered and not self.is_cancelled:
            self.is_delivered = True
            return True
        else:
            self.errors.append("cannot deliver")
            return False

    def cancel(self):
        if not self.is_shipped and not self.is_delivered:
            self.is_cancelled = True
            if self.is_paid:
                self.is_refunded = True
            return True
        else:
            self.errors.append("cannot cancel after shipping")
            return False
