# A class that keeps corresponding orders to together (1 buy order to 1 sell order)
class HedgedOrder:

    # Initializer / Instance Attributes
    def __init__(self, buy_order, sell_order):
        self.buy_order = buy_order
        self.sell_order = sell_order
