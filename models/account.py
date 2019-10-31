# A class that represents our brokerage account and all of its information
class Account:

    # Initializer / Instance Attributes
    def __init__(self, buying_power, portfolio_value, reg_t_buying_power):
        self.buying_power = buying_power
        self.portfolio_value = portfolio_value
        self.reg_t_buying_power = reg_t_buying_power
