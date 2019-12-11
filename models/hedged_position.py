# A class that keeps corresponding orders to together (1 buy order to 1 sell order)
class HedgedPosition:

    # Initializer / Instance Attributes
    def __init__(self, buy_position, sell_position, side):
        self.buy_position = buy_position
        self.sell_position = sell_position
        self.side = side

    def __eq__(self, other):
        if not isinstance(other, HedgedPosition):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.buy_position == other.buy_position and self.sell_position == other.sell_position and self.side == other.side
