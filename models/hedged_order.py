# A class that keeps corresponding orders to together (1 buy order to 1 sell order)
class HedgedOrder:

    # Initializer / Instance Attributes
    def __init__(self, buy_order, sell_order, side):
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.side = side

    def __eq__(self, other):
        if not isinstance(other, HedgedOrder):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.buy_order == other.buy_order and self.sell_order == other.sell_order and self.side == other.side
