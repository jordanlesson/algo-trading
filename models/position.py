# A class that represents a position and all its attributes
class Position:

    # Initializer / Instance Attributes
    def __init__(self, asset_id, symbol, qty, side, market_value, current_price):
        self.asset_id = asset_id
        self.symbol = symbol
        self.qty = qty
        self.side = side
        self.market_value = market_value
        self.currentPrice = current_price
