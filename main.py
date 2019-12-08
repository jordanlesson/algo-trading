import alpaca_trade_api as alpaca
from threading import Thread
import time
from models.stock import Stock
from models.order import Order
from models.hedged_order import HedgedOrder
from models.position import Position
from models.account import Account
from streams.account import account_updates
from streams.stocks import stock_stream_connection
from streams.trades import trade_updates


# Declaration of Alpaca API
alpaca_key_id = 'PKMHQUWERAMULK15DY13'
alpaca_secret_key = 'FpaNeZgF1mDg0J3nVuqWklSRfcRsh60ZioTOjccc'
alpaca_base_url = 'https://paper-api.alpaca.markets'

alpaca_api = alpaca.REST(
    key_id=alpaca_key_id,
    secret_key=alpaca_secret_key,
    base_url=alpaca_base_url,
)

# Global Declaration of Stock A data (empty)
stock_a = Stock(symbol="GOOG", price=None, bid_price=None, ask_price=None)

# Global Declaration of Stock B data (empty)
stock_b = Stock(symbol="GOOGL", price=None, bid_price=None, ask_price=None)

# Global Declaration of Alpaca account data (empty)
account = Account(buying_power=None, portfolio_value=None, reg_t_buying_power=None)

# Global Declaration of Arbitrary Values used in our algorithm (limit prices and credit and debit spreads)
original_buy_limit_price = float(
    input("Enter the adjustment for when we originally go to buy a stock (should be in dollars): "))
original_sell_limit_price = float(
    input("Enter the adjustment for when we originally go to sell a stock (should be positive and in dollars): "))
buy_limit_price_adjustment = float(
    input("Enter the amount of cents that should be added to whenever we adjust the buy limit price: "))
sell_limit_price_adjustment = float(
    input("Enter the amount of cents that should be added to whenever we adjust the sell limit price: "))
target_credit_spread = float(input("Enter Target Credit Spread: "))
target_debit_spread = float(input("Enter Target Debit Spread: "))
ratio_multiplier = int(input(
    "Enter the multiplier that makes the share price of the cheaper stock equal to the more expensive stock (ex. 1500 for BRK.B): "))
'''credit_focus = input("Should the algorithm only focus on credit spreads? ")
debit_focus = input("Should the algorithm only focus on debit spreads? ")'''

# Global Declaration of our positions, orders, and hedged orders (empty)
positions = []
orders = []
hedged_orders = []

hedging = False

# Alpaca has not made account updates useful yet
'''@conn.on(r'account_updates')
async def on_account_updates(conn, channel, account):
    print('account', account)'''


def main():
    # Local versions of our account data, current positions, and awaiting orders
    global account
    global positions

    # Retrieves initial account data before running algorithm
    # TODO: add a function that retrieves the historical data of stock A and stock B
    account = get_account()
    # positions = get_positions()
    # TODO: figure out a way to keep corresponding orders together off algorithm start-up
    alpaca_api.cancel_all_orders()

    if account is not None and positions is not None and orders is not None:
        # Runs stream connection functions in different threads
        Thread(target=stock_stream_connection).start()
        Thread(target=account_updates).start()
        Thread(target=trade_updates).start()
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
                    packaged_order = Order(id=order.id, asset_id=order.asset_id, symbol=order.symbol,
                                           limit_price=order.limit_price,
                                           order_type=order.order_type, qty=order.qty, side=order.side,
                                           time_in_force=order.time_in_force, status=order.status)
                    orders.append(packaged_order)
        return orders
    except Exception as error:
        print(error)
        return None


def spread_trader():
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


def check_orders(hedged_order):
    # TODO: make sure order is received before we check to see if it executed

    global hedging
    global positions

    hedging = True

    # Position is not hedged when orders are first submitted to Alpaca
    position_not_hedged = True

    # Orders exist when first submitted to Alpaca
    buy_order_exists = True
    sell_order_exists = True

    # Positions don't exist when first submitted to Alpaca because orders are awaiting execution
    buy_position_exists = False
    sell_position_exists = False

    buy_position = None
    sell_position = None

    # Initialization of the amount of times we check if our position is hedged
    check_count = 0

    expensive_class = None
    cheaper_class = None

    if stock_a.price >= stock_b.price:
        expensive_class = stock_a
        cheaper_class = stock_b
    else:
        expensive_class = stock_b
        cheaper_class = stock_a

    # Spread between the bid and ask
    bid_ask_spread = None

    if hedged_order.side == "debit":
        bid_ask_spread = expensive_class.bid_price - (cheaper_class.ask_price * ratio_multiplier)
    else:
        bid_ask_spread = expensive_class.ask_price - (cheaper_class.bid_price * ratio_multiplier)

    while position_not_hedged and check_count <= 10:

        check_count = check_count + 1
        buy_order = hedged_order.buy_order
        sell_order = hedged_order.sell_order

        if buy_order in orders:
            buy_order_exists = True
            order_index = orders.index(buy_order)
        else:
            buy_order_exists = False

        print("Buy Order Exists: {}".format(buy_order_exists))

        if sell_order in orders:
            sell_order_exists = True
            order_index = orders.index(sell_order)
        else:
            sell_order_exists = False

        print("Sell Order Exists: {}".format(sell_order_exists))

        if not buy_order_exists or not sell_order_exists:
            for position in positions:
                if buy_order.id == position.order_id and position.side == "long":
                    buy_position_exists = True
                    buy_position = position
                    buy_order.filled_qty = position.qty
                if sell_order.id == position.order_id and position.side == "short":
                    sell_position_exists = True
                    sell_position = position
                    sell_order.filled_qty = position.qty

        print("Buy Position Exists: {}".format(buy_position_exists))
        print("Sell Position Exists: {}".format(sell_position_exists))

        position_not_hedged = not buy_position_exists or not sell_position_exists

        if position_not_hedged and buy_order_exists and check_count % 3 == 0 and check_count != 0:
            print("Adjust buy order limit price")
            try:
                alpaca_api.cancel_order(buy_order.id)
                new_buy_order = alpaca_api.submit_order(symbol=buy_order.symbol,
                                                        qty=int(buy_order.qty) - int(buy_order.filled_qty),
                                                        side=buy_order.side, type=buy_order.order_type,
                                                        time_in_force=buy_order.time_in_force,
                                                        limit_price=float(
                                                            buy_order.limit_price) + float(bid_ask_spread * .10))

                packaged_buy_order = Order(id=new_buy_order.id, asset_id=new_buy_order.asset_id,
                                           symbol=new_buy_order.symbol,
                                           limit_price=float(new_buy_order.limit_price),
                                           order_type=new_buy_order.order_type, side=new_buy_order.side,
                                           qty=int(new_buy_order.qty),
                                           filled_qty=int(new_buy_order.filled_qty),
                                           time_in_force=new_buy_order.time_in_force,
                                           status=new_buy_order.status)

                hedged_order.buy_order = packaged_buy_order
            except Exception as error:
                print(error)

        if position_not_hedged and sell_order_exists and check_count % 3 == 0 and check_count != 0:
            print("Adjust sell order limit price")
            try:
                alpaca_api.cancel_order(sell_order.id)
                new_sell_order = alpaca_api.submit_order(symbol=sell_order.symbol,
                                                         qty=int(sell_order.qty) - int(sell_order.filled_qty),
                                                         side=sell_order.side, type=sell_order.order_type,
                                                         time_in_force=sell_order.time_in_force,
                                                         limit_price=float(sell_order.limit_price) - float(
                                                             bid_ask_spread * .10))

                packaged_sell_order = Order(id=new_sell_order.id, asset_id=new_sell_order.asset_id,
                                            symbol=new_sell_order.symbol,
                                            limit_price=float(new_sell_order.limit_price),
                                            order_type=new_sell_order.order_type, side=new_sell_order.side,
                                            qty=int(new_sell_order.qty),
                                            filled_qty=int(new_sell_order.filled_qty),
                                            time_in_force=new_sell_order.time_in_force,
                                            status=new_sell_order.status)

                hedged_order.sell_order = packaged_sell_order
            except Exception as error:
                print(error)

        if position_not_hedged and check_count >= 10:
            try:

                if buy_order_exists:
                    alpaca_api.cancel_order(buy_order.id)

                    print("Buy Order Filled Qty: {}".format(buy_order.filled_qty))
                    if buy_position_exists and buy_position is not None and buy_order.filled_qty != 0:
                        Thread(target=liquidate_position, args=(buy_position, int(buy_order.filled_qty))).start()

                elif buy_position_exists and buy_position:
                    Thread(target=liquidate_position, args=(buy_position, int(buy_order.qty))).start()

                if sell_order_exists:
                    alpaca_api.cancel_order(sell_order.id)

                    print("Sell Order Filled Qty: {}".format(sell_order.filled_qty))
                    if sell_position_exists and sell_position is not None and sell_order.filled_qty != 0:
                        Thread(target=liquidate_position, args=(sell_position, int(sell_order.filled_qty))).start()

                elif sell_position_exists and sell_position is not None:
                    Thread(target=liquidate_position, args=(sell_position, int(sell_order.qty))).start()

                position_not_hedged = False

                print("Orders canceled and positions liquidated")

            except Exception as error:
                print(error)
                print("Could not cancel our orders and liquidate our positions")

        if not position_not_hedged:
            if (buy_position_exists and sell_position_exists) or (not buy_position_exists and not sell_position_exists):
                positions = []
                hedging = False

        print(check_count)

        time.sleep(5.0)


async def liquidate_position(position, qty):
    global positions
    global hedging

    current_position = position

    position_exists = True

    submitted_order = None

    stock_data = None
    if position.symbol == stock_a.symbol:
        stock_data = stock_a
    else:
        stock_data = stock_b

    check_count = 0
    while position_exists:

        check_count = check_count + 1

        # if submitted_order is None:
        if current_position in positions:
            position_exists = True
            position_index = positions.index(position)
            current_position.qty = positions[position_index].qty
        else:
            position_exists = False
        print("LIQUIDATION POSITION EXISTS: {}".format(position_exists))
        '''else:
            position_exists = False
            for currentPosition in positions:
                if currentPosition.order_id == submitted_order.id:
                    position_exists = True'''

        order = None

        try:
            print(position.symbol)

            if position.side == "long" and position_exists:
                if check_count == 1:
                    print("Placing liquidation sell order")

                    order = await alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell", type="limit",
                                                          limit_price=float(stock_data.bid_price) + 0.20,
                                                          time_in_force="gtc")

                if check_count == 3:
                    print("Adjusting liquidation sell order by .10 cents")

                    if submitted_order in orders:
                        await alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = await alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell",
                                                              type="limit",
                                                              limit_price=float(stock_data.bid_price) + 0.10,
                                                              time_in_force="gtc")

                if check_count == 6:
                    print("Adjusting liquidation sell order by market order")

                    position_exists = False

                    if submitted_order in orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell", type="market",
                                                        time_in_force="gtc")
            elif position.side == "short" and position_exists:
                if check_count == 1:
                    print("Placing liquidation buy order")

                    order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy", type="limit",
                                                    limit_price=float(stock_data.ask_price) - 0.20, time_in_force="gtc")

                if check_count == 3:
                    print("Adjusting liquidation buy order by .10 cents")

                    if submitted_order in orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy", type="limit",
                                                        limit_price=float(stock_data.ask_price) - 0.10,
                                                        time_in_force="gtc")

                if check_count == 6:
                    print("Adjusting liquidation buy order by market order")

                    position_exists = False

                    if submitted_order in orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy", type="market",
                                                        time_in_force="gtc")

        except Exception as error:
            print(error)
            position_exists = False

        if order is not None and check_count < 6:
            submitted_order = Order(id=order.id, asset_id=order.asset_id, symbol=order.symbol,
                                    limit_price=float(order.limit_price),
                                    order_type=order.order_type, side=order.side, qty=int(order.qty),
                                    filled_qty=int(order.filled_qty), time_in_force=order.time_in_force,
                                    status=order.status)

        if not position_exists:
            print("Position Liquidated")
            positions = []
            hedging = False

        time.sleep(5.0)


# noinspection PyArgumentList,PyArgumentList,PyArgumentList,PyArgumentList
def open_position(expensive_class, cheaper_class, side, ratio):
    global hedging

    try:
        if side == "credit" and account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price and not hedging:

            # Shows a flag to the rest of the program that it is currently trying to hedge a position and no further positions should be opened until hedged or canceled
            hedging = True

            sell_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='sell', type='limit',
                                                 limit_price=expensive_class.ask_price - (
                                                         2 * original_sell_limit_price),
                                                 time_in_force='gtc')
            buy_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='buy', type='limit',
                                                limit_price=cheaper_class.bid_price + original_buy_limit_price,
                                                time_in_force='gtc')

            packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=expensive_class.symbol,
                                        limit_price=float(sell_order.limit_price),
                                        order_type=sell_order.order_type, side=sell_order.side, qty=int(sell_order.qty),
                                        filled_qty=int(sell_order.filled_qty), time_in_force=sell_order.time_in_force,
                                        status=sell_order.status)

            packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=cheaper_class.symbol,
                                       limit_price=float(buy_order.limit_price),
                                       order_type=buy_order.order_type, side=buy_order.side, qty=int(buy_order.qty),
                                       filled_qty=int(buy_order.filled_qty), time_in_force=buy_order.time_in_force,
                                       status=buy_order.status)

            hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side=side)

            hedged_orders.append(hedged_order)

            print('Credit Spread Order Placed')

            Thread(target=check_orders, args=(hedged_order,)).start()  # Problem with parenthesis

        elif side == "debit" and account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price and not hedging:

            # Shows a flag to the rest of the program that it is currently trying to hedge a position and no further positions should be opened until hedged or canceled
            hedging = True

            sell_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='sell', type='limit',
                                                 limit_price=cheaper_class.ask_price - original_sell_limit_price,
                                                 time_in_force='gtc')
            buy_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='buy', type='limit',
                                                limit_price=expensive_class.bid_price + (2 * original_buy_limit_price),
                                                time_in_force='gtc')

            packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=cheaper_class.symbol,
                                        limit_price=float(sell_order.limit_price),
                                        order_type=sell_order.order_type, side=sell_order.side, qty=int(sell_order.qty),
                                        filled_qty=int(sell_order.filled_qty), time_in_force=sell_order.time_in_force,
                                        status=sell_order.status)

            packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=expensive_class.symbol,
                                       limit_price=float(buy_order.limit_price),
                                       order_type=buy_order.order_type, side=buy_order.side, qty=int(buy_order.qty),
                                       filled_qty=int(buy_order.filled_qty), time_in_force=buy_order.time_in_force,
                                       status=buy_order.status)

            hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side=side)

            hedged_orders.append(hedged_order)

            print('Debit Spread Order Placed')

            Thread(target=check_orders, args=(hedged_order,)).start()

    except Exception as error:
        hedging = False
        print(error)


# This block of code is the catalyst to running our algorithm and stock market checks
if __name__ == '__main__':
    main()
