# A class that represents a position and all its attributes
class Position:

    # Initializer / Instance Attributes
    def __init__(self, asset_id, order_id, symbol, qty, side):
        self.asset_id = asset_id
        self.order_id = order_id
        self.symbol = symbol
        self.qty = qty
        self.side = side

    def __eq__(self, other):
        if not isinstance(other, Position):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.order_id == other.order_id and self.asset_id == other.asset_id and self.symbol == other.symbol and self.side == other.side
