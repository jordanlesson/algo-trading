# A class that represents a particular stock and its data
class Stock:

    # Initializer / Instance Attributes
    def __init__(self, symbol, price, bid_price, ask_price):
        self.symbol = symbol
        self.price = price
        self.bid_price = bid_price
        self.ask_price = ask_price
