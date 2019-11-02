import websocket
import json
import alpaca_trade_api as alpaca
from alpaca_trade_api import StreamConn
from threading import Thread
from models.stock import Stock
from models.order import Order
from models.hedged_order import HedgedOrder
from models.position import Position
from models.account import Account
import time

# Declaration of Alpaca API
# noinspection SpellCheckingInspection
alpaca_api = alpaca.REST(
    key_id='PK9W3C1GMJM9X919CMPY',
    secret_key='ws4CXCL1glbV9glqxY/uJTNjTguWBAkP0vDxvkYw',
    base_url='https://paper-api.alpaca.markets',
)

# Declaration of stream
conn = StreamConn(
    key_id="PK9W3C1GMJM9X919CMPY",
    secret_key="ws4CXCL1glbV9glqxY/uJTNjTguWBAkP0vDxvkYw",
    base_url="https://paper-api.alpaca.markets",
)

# Global Declaration of Stock A data (empty)
stock_a = Stock(symbol=input("Enter Stock A Symbol *IN ALL CAPS*: "), price=None, bid_price=None, ask_price=None)

# Global Declaration of Stock B data (empty)
stock_b = Stock(symbol=input("Enter Stock B Symbol *IN ALL CAPS*: "), price=None, bid_price=None, ask_price=None)

# Global Declaration of Alpaca account data (empty)
account = Account(buying_power=None, portfolio_value=None, reg_t_buying_power=None)

# Global Declaration of Arbitrary Values used in our algorithm (limit prices and credit and debit spreads)
original_buy_limit_price = float(input("Enter the adjustment for when we originally go to buy a stock (should be in cents): "))
original_sell_limit_price = float(input("Enter the adjustment for when we originally go to sell a stock (should be positive and in cents): "))
buy_limit_price_adjustment = float(input("Enter the amount of cents that should be added to whenever we adjust the buy limit price: "))
sell_limit_price_adjustment = float(input("Enter the amount of cents that should be added to whenever we adjust the sell limit price: "))
target_credit_spread = float(input("Enter Target Credit Spread: "))
target_debit_spread = float(input("Enter Target Debit Spread: "))
ratio_multiplier = float(input("Enter the multiplier that makes the share price of the cheaper stock equal to the more expensive stock (ex. 1500 for BRK.B): "))


# Global Declaration of our positions, orders, and hedged orders (empty)
positions = []
orders = []
hedged_orders = []

hedging = False

# Alpaca has not made account updates useful yet
'''@conn.on(r'account_updates')
async def on_account_updates(conn, channel, account):
    print('account', account)'''


# Function that is called whenever an order update occurs (new orders, fills, partial fills, cancels, etc...)
# noinspection SpellCheckingInspection,PyShadowingNames
@conn.on(r'trade_updates')
async def on_trade_updates(conn, channel, data):
    global orders
    global hedged_orders

    order_data = data
    order = order_data.order
    packaged_order = Order(id=order["id"], asset_id=order["asset_id"],symbol=order["symbol"], limit_price=order["limit_price"],
                           order_type=order["order_type"], qty=order["qty"],
                           filled_qty=order["filled_qty"], side=order["side"], time_in_force=order["time_in_force"],
                           status=order["status"])

    if order_data.event == "new":
        orders.append(packaged_order)
    elif order_data.event == "fill":
        if orders.count(packaged_order) > 0:
            orders.remove(packaged_order)
    elif order_data.event == "partial_fill":
        if orders.count(packaged_order) > 0:
            order_index = orders.index(packaged_order)
            orders[order_index] = packaged_order
    elif order_data.event == "canceled" or order_data.event == "expired":
        if orders.count(packaged_order) > 0:
            orders.remove(packaged_order)


def main():
    # Local versions of our account data, current positions, and awaiting orders
    global account
    global positions
    # global orders

    # Retrieves initial account data before running algorithm
    # TODO: add a function that retrieves the historical data of stock A and stock B
    account = get_account()
    positions = get_positions()
    # TODO: figure out a way to keep corresponding orders together off algorithm start-up
    alpaca_api.cancel_all_orders()

    if account is not None and positions is not None and orders is not None:
        # Runs stream connection functions in different threads
        Thread(target=stock_stream_connection).start()
        Thread(target=account_updates).start()
        Thread(target=position_updates).start()
        Thread(target=order_updates).start()
    else:
        print("Error Occurred: Either a failure in fetching account data, positions, or orders")


# noinspection PyShadowingNames
def get_account():
    try:
        account_info = alpaca_api.get_account()
        account = Account(buying_power=float(account_info.buying_power),
                          portfolio_value=float(account_info.portfolio_value),
                          reg_t_buying_power=float(account_info.regt_buying_power))
        return account
    except Exception as error:
        print(error)
        return None


# noinspection PyShadowingNames
def get_positions():
    positions = []

    try:
        position_list = alpaca_api.list_positions()
        if len(position_list) != 0:
            for position in position_list:
                packaged_position = Position(asset_id=position.asset_id, symbol=position.symbol, qty=position.qty, side=position.side,
                                             market_value=position.market_value, current_price=position.current_price)
                positions.append(packaged_position)
        return positions
    except Exception as error:
        print(error)
        return None


# noinspection PyShadowingNames,PyArgumentList
def get_orders():
    orders = []

    try:
        order_list = alpaca_api.list_orders()
        if len(order_list) != 0:
            filtered_order_list = list(
                filter(lambda o: o.canceled_at is None and o.filled_at is None and o.failed_at is None, order_list))
            if len(filtered_order_list) != 0:
                for order in filtered_order_list:
                    packaged_order = Order(id=order.id, asset_id=order.asset_id, symbol=order.symbol, limit_price=order.limit_price,
                                           order_type=order.order_type, qty=order.qty, side=order.side,
                                           time_in_force=order.time_in_force, status=order.status)
                    orders.append(packaged_order)
        return orders
    except Exception as error:
        print(error)
        return None


def account_updates():
    global account

    while True:
        try:
            account_info = alpaca_api.get_account()
            account = Account(buying_power=float(account_info.buying_power),
                              portfolio_value=float(account_info.portfolio_value),
                              reg_t_buying_power=float(account_info.regt_buying_power))
        except Exception as error:
            print(error)
        time.sleep(0.5)


def order_updates():
    conn.run(['trade_updates'])


def position_updates():
    global positions

    current_positions = []

    while True:
        try:
            position_list = alpaca_api.list_positions()
            if len(position_list) != 0:
                for position in position_list:
                    packaged_position = Position(asset_id=position.asset_id, symbol=position.symbol, qty=position.qty, side=position.side,
                                                 market_value=position.market_value,
                                                 current_price=position.current_price)
                    current_positions.append(packaged_position)
                positions = current_positions
            else:
                positions = []

        except Exception as error:
            print(error)

        time.sleep(0.5)


def stock_stream_connection():
    print('Started Running')

    # Subscribes WebSocket to stocks
    ws = websocket.WebSocketApp("wss://alpaca.socket.polygon.io/stocks", on_message=on_stock_update, on_open=on_open,
                                on_close=on_close, on_error=on_error)

    ws.on_open = on_open
    ws.run_forever()


# Function that gets called whenever a stocks bid price, ask price, or share price changes
def on_stock_update(ws, message):
    stock_data = json.loads(message)

    global stock_a
    global stock_b

    # Filters out stock's trade info (last trade)
    if stock_data[0]["ev"] == 'T':
        stock_a_trade = next((stock for stock in stock_data if stock["sym"] == stock_a.symbol), {
            "sym": stock_a.symbol,
            "p": stock_a.price,
            "bp": stock_a.bid_price,
            "ap": stock_a.ask_price,
        })
        if stock_a_trade["p"] is not None:
            stock_a.price = stock_a_trade["p"]

        stock_b_trade = next((stock for stock in stock_data if stock["sym"] == stock_b.symbol), {
            "sym": stock_b.symbol,
            "p": stock_b.price,
            "bp": stock_b.bid_price,
            "ap": stock_b.ask_price,
        })
        if stock_b_trade["p"] is not None:
            stock_b.price = stock_b_trade["p"]

    # Filters out stock's quote (current bid and ask price)
    if stock_data[0]["ev"] == 'Q':
        stock_a_quote = next((stock for stock in stock_data if stock["sym"] == stock_a.symbol), {
            "sym": stock_a.symbol,
            "p": stock_a.price,
            "bp": stock_a.bid_price,
            "ap": stock_a.ask_price,
        })
        if stock_a_quote["bp"] is not None:
            stock_a.bid_price = stock_a_quote["bp"]
        if stock_a_quote["ap"] is not None:
            stock_a.ask_price = stock_a_quote["ap"]

        stock_b_quote = next((stock for stock in stock_data if stock["sym"] == stock_b.symbol), {
            "sym": stock_b.symbol,
            "p": stock_b.price,
            "bp": stock_b.bid_price,
            "ap": stock_b.ask_price,
        })
        if stock_b_quote["bp"] is not None:
            stock_b.bid_price = stock_b_quote["bp"]
        if stock_b_quote["ap"] is not None:
            stock_b.ask_price = stock_b_quote["ap"]

    market_is_open = True
    stock_data_exists = check_stock_data()

    if market_is_open and stock_data_exists:
        # Run Algorithm Here

        # Declaration of expensive and cheaper class (empty)
        expensive_class = None
        cheaper_class = None

        if stock_a.price >= stock_b.price:
            expensive_class = stock_a
            cheaper_class = stock_b
        else:
            expensive_class = stock_b
            cheaper_class = stock_a

        credit_spread = expensive_class.ask_price - (cheaper_class.bid_price * ratio_multiplier)
        debit_spread = expensive_class.bid_price - (cheaper_class.ask_price * ratio_multiplier)

        if credit_spread > target_credit_spread and not hedging:

            open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='credit',
                          ratio=ratio_multiplier)

        elif debit_spread < target_debit_spread and not hedging:

            open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='debit',
                          ratio=ratio_multiplier)


def on_error(ws, error):
    # ws.send('{"action":"unsubscribe","params":"Q.GOOG, Q.GOOGL"}')
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send('{"action":"auth","params":"AKK5WUTECIGM1G8XTN3C"}')
    ws.send('{"action":"subscribe","params":"Q.{},T.{},Q.{},T.{}"}'.format(stock_a.symbol, stock_a.symbol, stock_b.symbol, stock_b.symbol))


def check_market():
    try:
        clock = alpaca_api.get_clock()
        if clock.is_open:
            return True
        else:
            return False
    except Exception as error:
        print(error)
        return False


def check_stock_data():
    if stock_a.price is not None and stock_a.bid_price is not None and stock_a.ask_price is not None and stock_b.price is not None and stock_b.bid_price is not None and stock_b.ask_price is not None:
        return True
    else:
        return False


def check_orders(hedged_order):
    # TODO: make sure order is received before we check to see if it executed

    # Position is not hedged when orders are first submitted to Alpaca
    position_not_hedged = False

    # Orders exist when first submitted to Alpaca
    buy_order_exists = True
    sell_order_exists = True

    # Positions don't exist when first submitted to Alpaca because orders are awaiting execution
    buy_position_exists = False
    sell_position_exists = False

    # Initialization of the amount of times we check if our position is hedged
    check_count = 0

    while position_not_hedged:
        buy_order = hedged_order.buy_order
        sell_order = hedged_order.sell_order

        for order in orders:
            if buy_order != order:
                buy_order_exists = False
            else:
                hedged_order.buy_order.filled_qty = order.filled_qty

            if sell_order != order:
                sell_order_exists = False
            else:
                hedged_order.sell_order.filled_qty = order.filled_qty

        if not buy_order_exists or not sell_order_exists:
            for position in positions:
                if buy_order.asset_id == position.asset_id:
                    buy_position_exists = True
                if sell_order.asset_id == position.asset_id:
                    sell_position_exists = True

        position_not_hedged = not buy_position_exists or not sell_position_exists

        if position_not_hedged and buy_order_exists and check_count % 3 == 0 and check_count != 0:
            print("Adjust buy order limit price")
            try:
                alpaca_api.cancel_order(buy_order.id)
                new_buy_order = alpaca_api.submit_order(symbol=buy_order.symbol,
                                                        qty=int(buy_order.qty - buy_order.filled_qty),
                                                        side=buy_order.side, type=buy_order.order_type,
                                                        time_in_force=buy_order.time_in_force,
                                                        limit_price=float(buy_order.limit_price + buy_limit_price_adjustment))
                hedged_order.buy_order = new_buy_order
            except Exception as error:
                print(error)

        if position_not_hedged and sell_order_exists and check_count % 3 == 0 and check_count != 0:
            print("Adjust sell order limit price")
            try:
                alpaca_api.cancel_order(sell_order.id)
                new_sell_order = alpaca_api.submit_order(symbol=sell_order.symbol,
                                                         qty=int(sell_order.qty - sell_order.filled_qty),
                                                         side=sell_order.side, type=sell_order.order_type,
                                                         time_in_force=sell_order.time_in_force,
                                                         limit_price=float(sell_order.limit_price - sell_limit_price_adjustment))
                hedged_order.sell_order = new_sell_order
            except Exception as error:
                print(error)

        if not position_not_hedged:
            global hedging

            hedging = False

        check_count = check_count + 1

    time.sleep(5.0)


# noinspection PyArgumentList,PyArgumentList,PyArgumentList,PyArgumentList
def open_position(expensive_class, cheaper_class, side, ratio):

    global hedging

    # Shows a flag to the rest of the program that it is currently trying to hedge a position and no further positions should be opened until hedged or canceled
    hedging = True

    try:
        if side == "credit" and account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price:

            sell_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='sell', type='limit',
                                                 limit_price=expensive_class.ask_price - original_sell_limit_price, time_in_force='gtc')
            buy_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='buy', type='limit',
                                                limit_price=cheaper_class.bid_price + original_buy_limit_price, time_in_force='gtc')

            packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=expensive_class.symbol,
                                        limit_price=sell_order.limit_price,
                                        order_type=sell_order.order_type, side=sell_order.side, qty=sell_order.qty,
                                        filled_qty=sell_order.filled_qty, time_in_force=sell_order.time_in_force,
                                        status=sell_order.status)

            packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=cheaper_class.symbol, limit_price=buy_order.limit_price,
                                       order_type=buy_order.order_type, side=buy_order.side, qty=buy_order.qty,
                                       filled_qty=buy_order.filled_qty, time_in_force=buy_order.time_in_force,
                                       status=buy_order.status)

            hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side=side)

            hedged_orders.append(hedged_order)

            print('Credit Spread Bought')

            Thread(target=check_orders(hedged_order)).start()

        elif side == "debit" and account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price:

            sell_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='sell', type='limit',
                                                 limit_price=cheaper_class.ask_price - original_sell_limit_price, time_in_force='gtc')
            buy_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='buy', type='limit',
                                                limit_price=expensive_class.bid_price + original_buy_limit_price, time_in_force='gtc')

            packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=cheaper_class.symbol,
                                        limit_price=sell_order.limit_price,
                                        order_type=sell_order.order_type, side=sell_order.side, qty=sell_order.qty,
                                        filled_qty=sell_order.filled_qty, time_in_force=sell_order.time_in_force,
                                        status=sell_order.status)

            packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=expensive_class.symbol,
                                       limit_price=buy_order.limit_price,
                                       order_type=buy_order.order_type, side=buy_order.side, qty=buy_order.qty,
                                       filled_qty=buy_order.filled_qty, time_in_force=buy_order.time_in_force,
                                       status=buy_order.status)

            hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side=side)

            hedged_orders.append(hedged_order)

            print('Debit Spread Bought')

            Thread(target=check_orders(hedged_order)).start()

    except Exception as error:
        print(error)


# This block of code is the catalyst to running our algorithm and stock market checks
if __name__ == '__main__':
    main()
