# A class that represents an order and all its attributes
class Order:

    # Initializer / Instance Attributes
    def __init__(self, id, symbol, limit_price, order_type, qty, filled_qty, side, time_in_force, status):
        self.id = id
        self.symbol = symbol
        self.limit_price = limit_price
        self.order_type = order_type
        self.qty = qty
        self.filled_qty = filled_qty
        self.side = side
        self.time_in_force = time_in_force
        self.status = status
