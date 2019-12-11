from config import alpaca_api
from threading import Thread
import concurrent.futures
from multiprocessing import Queue
import time
from models.order import Order
from models.position import Position
from models.hedged_position import HedgedPosition
from models.account import Account
import streams.account as account_stream
import streams.stocks as stock_stream
import streams.trades as trades_stream
from utils.positions import open_credit_position, open_debit_position

# Global Declaration of Arbitrary Values used in our algorithm (limit prices and credit and debit spreads)
target_credit_spread = float(input("Enter Target Credit Spread: "))
target_debit_spread = float(input("Enter Target Debit Spread: "))
ratio_multiplier = int(input(
    "Enter the multiplier that makes the share price of the cheaper stock equal to the more expensive stock (ex. 1500 for BRK.B): "))

'''credit_focus = input("Should the algorithm only focus on credit spreads? ")
debit_focus = input("Should the algorithm only focus on debit spreads? ")'''

hedged_positions = []

hedging = False
closing = False

# Alpaca has not made account updates useful yet
'''@conn.on(r'account_updates')
async def on_account_updates(conn, channel, account):
    print('account', account)'''


def main():
    # Retrieves initial account data before running algorithm
    # TODO: add a function that retrieves the historical data of stock A and stock B
    # account = get_account()
    # TODO: figure out a way to keep corresponding orders together off algorithm start-up
    alpaca_api.cancel_all_orders()

    # Runs stream connection functions in different threads
    Thread(target=stock_stream.stock_stream_connection).start()
    Thread(target=account_stream.account_updates).start()
    Thread(target=trades_stream.trade_updates).start()

    # Listens to whether the stock stream has data and performs algorithm if data exists
    Thread(target=spread_trader).start()


# noinspection PyShadowingNames
def get_account():
    try:
        account_info = alpaca_api.get_account()
        account_data = Account(buying_power=float(account_info.buying_power),
                               portfolio_value=float(account_info.portfolio_value),
                               reg_t_buying_power=float(account_info.regt_buying_power))
        return account_data
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


def stock_data_check():
    if stock_stream.stock_a.price is not None and stock_stream.stock_a.bid_price is not None and stock_stream.stock_a.ask_price is not None and stock_stream.stock_b.price is not None and stock_stream.stock_b.bid_price is not None and stock_stream.stock_b.ask_price is not None:
        return True
    else:
        return False


def account_data_check():
    if account_stream.account.buying_power is not None and account_stream.account.reg_t_buying_power is not None and account_stream.account.portfolio_value is not None:
        return True
    else:
        return False


def spread_trader():
    global hedging
    global closing

    market_is_open = True

    # While market is open, check to see if we we have stock and account streams running
    while market_is_open:
        stock_data_exists = stock_data_check()
        account_data_exists = account_data_check()

        # If stock data and account info streams are running, then run our algorithm
        if stock_data_exists and account_data_exists:

            # Declaration of expensive and cheaper class (empty)
            expensive_class = None
            cheaper_class = None

            # Determining which stock is more expensive so we can calculate the spread between the bid and ask
            if stock_stream.stock_a.price >= stock_stream.stock_b.price:
                expensive_class = stock_stream.stock_a
                cheaper_class = stock_stream.stock_b
            else:
                expensive_class = stock_stream.stock_b
                cheaper_class = stock_stream.stock_a

            # The spread (in dollars) between the bid and ask of the stocks (ratio is accounted for)
            credit_spread = expensive_class.ask_price - (cheaper_class.bid_price * ratio_multiplier)
            debit_spread = expensive_class.bid_price - (cheaper_class.ask_price * ratio_multiplier)

            hedged_order = None

            ''' if the current credit spread is greater than our target credit spread, we have enough buying power, and
            we are not currently trying to hedge another position, then open a new credit and close all debits'''
            if credit_spread > target_credit_spread and account_stream.account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price and not hedging:

                hedged_order = open_credit_position(expensive_class=expensive_class, cheaper_class=cheaper_class,
                                                    spread=credit_spread,
                                                    ratio=ratio_multiplier)

                '''if not closing:
                    closing = True
                    for hedged_position in hedged_positions:
                        if hedged_position.side == "debit":
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                close_position = executor.submit(open_credit_position, (
                                    expensive_class, cheaper_class, credit_spread, ratio_multiplier))
                                close_hedged_order = close_position.result()

                                if close_hedged_order is not None:
                                    Thread(target=check_orders, args=(close_hedged_order,)).start()
                                else:
                                    print("Failure to close credit position")'''

            elif debit_spread < target_debit_spread and account_stream.account.buying_power >= cheaper_class.ask_price + expensive_class.bid_price and not hedging:

                hedged_order = open_debit_position(expensive_class=expensive_class, cheaper_class=cheaper_class,
                                                   spread=debit_spread,
                                                   ratio=ratio_multiplier)

                '''if not closing:
                    closing = True
                    for hedged_position in hedged_positions:
                        if hedged_position.side == "credit":
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                close_position = executor.submit(open_debit_position, (
                                expensive_class, cheaper_class, debit_spread, ratio_multiplier))
                                close_hedged_order = close_position.result()

                                if close_hedged_order is not None:
                                    Thread(target=check_orders, args=(close_hedged_order,)).start()
                                else:
                                    print("Failure to close credit position")'''

            # If we submitted orders to open a position, then check to see if the orders executed
            if hedged_order is not None:

                # Flag the rest of the program to show that we are currently attempting to hedge a position
                hedging = True

                que = Queue()

                # Checks orders to see if they executed, returns a leg if doesn't fully hedge
                check_orders_thread = Thread(target=lambda q, arg1: q.put(check_orders(arg1)),
                                             args=(que, hedged_order,))
                check_orders_thread.start()
                check_orders_thread.join()

                executed_leg = que.get()

                # If only one side of our position hedges, liquidate that position
                if executed_leg is not None and executed_position is not None:
                    executed_position = executed_leg[0]
                    executed_position_qty = executed_leg[1]

                    Thread(target=liquidate_position, args=(executed_position, executed_position_qty,)).start()

                else:
                    # Flag to our program that our position didn't execute or our position hedged so we can open more positions
                    hedging = False


def check_orders(hedged_order):
    # TODO: make sure order is received before we check to see if it executed

    # Position is not hedged when orders are first submitted to Alpaca
    position_hedged = False

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

    # Determines the more expensive and cheaper stock in order to calculate the spread between the bid and ask
    if stock_stream.stock_a.price >= stock_stream.stock_b.price:
        expensive_class = stock_stream.stock_a
        cheaper_class = stock_stream.stock_b
    else:
        expensive_class = stock_stream.stock_b
        cheaper_class = stock_stream.stock_a

    # Spread between the bid and ask for adjusting orders
    spread = None
    if hedged_order.side == "debit":
        spread = expensive_class.bid_price - (cheaper_class.ask_price * ratio_multiplier)
    else:
        spread = expensive_class.ask_price - (cheaper_class.bid_price * ratio_multiplier)

    # While our position is not hedged, check to see if our orders executed or not
    while not position_hedged:

        # Increments the amount of times we check to see if our orders have executed or not
        check_count = check_count + 1

        buy_order = hedged_order.buy_order
        sell_order = hedged_order.sell_order

        # The dollar amount that our limit order should be adjusted by
        spread_adjuster = (spread * .10) * (check_count / 3)

        # Checks whether a buy order exists in our orders stream
        if buy_order in trades_stream.orders:
            buy_order_exists = True
        else:
            buy_order_exists = False

        # Checks whether a sell order exists in our orders stream
        if sell_order in trades_stream.orders:
            sell_order_exists = True
        else:
            sell_order_exists = False

        print("Buy Order Exists: {}".format(buy_order_exists))
        print("Sell Order Exists: {}".format(sell_order_exists))

        # Checks whether our buy or sell order executed
        if not buy_order_exists or not sell_order_exists:
            for position in trades_stream.positions:
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

        position_hedged = buy_position_exists and sell_position_exists

        # If we are not hedged and a buy order exists, submit a new buy order every three times we check
        if not position_hedged and buy_order_exists and check_count % 3 == 0 and check_count != 0 and check_count != 12:

            print("Adjust buy order limit price")
            try:
                alpaca_api.cancel_order(buy_order.id)
                new_buy_order = alpaca_api.submit_order(symbol=buy_order.symbol,
                                                        qty=int(buy_order.qty) - int(
                                                            buy_order.filled_qty),
                                                        side=buy_order.side, type=buy_order.order_type,
                                                        time_in_force=buy_order.time_in_force,
                                                        limit_price=float(
                                                            buy_order.limit_price) + float(
                                                            spread_adjuster))

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

        # If we are not hedged and a sell order exists, submit a new sell order every three times we check
        if not position_hedged and sell_order_exists and check_count % 3 == 0 and check_count != 0 and check_count != 12:
            print("Adjust sell order limit price")
            try:
                alpaca_api.cancel_order(sell_order.id)
                new_sell_order = alpaca_api.submit_order(symbol=sell_order.symbol,
                                                         qty=int(sell_order.qty) - int(
                                                             sell_order.filled_qty),
                                                         side=sell_order.side,
                                                         type=sell_order.order_type,
                                                         time_in_force=sell_order.time_in_force,
                                                         limit_price=float(
                                                             sell_order.limit_price) - float(
                                                             spread_adjuster))

                packaged_sell_order = Order(id=new_sell_order.id, asset_id=new_sell_order.asset_id,
                                            symbol=new_sell_order.symbol,
                                            limit_price=float(new_sell_order.limit_price),
                                            order_type=new_sell_order.order_type,
                                            side=new_sell_order.side,
                                            qty=int(new_sell_order.qty),
                                            filled_qty=int(new_sell_order.filled_qty),
                                            time_in_force=new_sell_order.time_in_force,
                                            status=new_sell_order.status)

                hedged_order.sell_order = packaged_sell_order
            except Exception as error:
                print(error)

        # If our position isn't hedged and we've check three times, return the executed leg if it exists
        if not position_hedged and check_count >= 12:
            try:
                if buy_order_exists:
                    alpaca_api.cancel_order(buy_order.id)
                    return [buy_position, buy_order.filled_qty]

                if sell_order_exists:
                    alpaca_api.cancel_order(sell_order.id)
                    return [sell_position, sell_order.filled_qty]

                print("Orders canceled and positions liquidated")

                return None
            except Exception as error:
                print(error)
                print("Could not cancel our orders and liquidate our positions")
                return None

        # If position is hedged, then add it to our list of hedged_positions
        if position_hedged:
            buy_position = Position(asset_id=buy_order.asset_id, order_id=buy_order.id, symbol=buy_order.symbol,
                                    qty=buy_order.filled_qty, side="long")
            sell_position = Position(asset_id=sell_order.asset_id, order_id=sell_order.id, symbol=sell_order.symbol,
                                     qty=sell_order.filled_qty, side="short")

            hedged_position = HedgedPosition(buy_position=buy_position, sell_position=sell_position,
                                             side=hedged_order.side)

            hedged_positions.append(hedged_position)

            return None

        print(check_count)

        time.sleep(10.0)

    return None


def liquidate_position(position, qty):
    # global positions
    global hedging

    current_position = position

    position_exists = True

    submitted_order = None

    stock_data = None
    if position.symbol == stock_stream.stock_a.symbol:
        stock_data = stock_stream.stock_a
    else:
        stock_data = stock_stream.stock_b

    bid_ask_spread = stock_data.ask_price - stock_data.bid_price

    check_count = 0
    while position_exists:

        check_count = check_count + 1

        spread_adjuster = (bid_ask_spread * .10) * (check_count / 3)

        # if submitted_order is None:
        if current_position in trades_stream.positions:
            position_exists = True
            position_index = trades_stream.positions.index(position)
            current_position.qty = trades_stream.positions[position_index].qty
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

                    order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell", type="limit",
                                                    limit_price=float(stock_data.bid_price) + (
                                                            bid_ask_spread * .10),
                                                    time_in_force="gtc")

                if check_count != 0 and check_count % 3 == 0 and not check_count == 12:
                    if submitted_order in trades_stream.orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell",
                                                        type="limit",
                                                        limit_price=float(stock_data.bid_price) + spread_adjuster,
                                                        time_in_force="gtc")

                if check_count == 12:
                    print("Adjusting liquidation sell order by market order")

                    position_exists = False

                    if submitted_order in trades_stream.orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="sell", type="market",
                                                        time_in_force="gtc")

            elif position.side == "short" and position_exists:

                if check_count == 1:
                    print("Placing liquidation buy order")

                    order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy", type="limit",
                                                    limit_price=float(stock_data.ask_price) - (bid_ask_spread * .10),
                                                    time_in_force="gtc")

                if check_count != 0 and check_count % 3 == 0 and not check_count == 12:
                    if submitted_order in trades_stream.orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy",
                                                        type="limit",
                                                        limit_price=float(stock_data.bid_price) - spread_adjuster,
                                                        time_in_force="gtc")

                if check_count == 12:
                    print("Adjusting liquidation buy order by market order")

                    position_exists = False

                    if submitted_order in trades_stream.orders:
                        alpaca_api.cancel_order(submitted_order.id)
                        time.sleep(3.0)
                        order = alpaca_api.submit_order(symbol=position.symbol, qty=qty, side="buy", type="market",
                                                        time_in_force="gtc")

        except Exception as error:
            print(error)
            position_exists = False

        if order is not None and check_count < 12:
            submitted_order = Order(id=order.id, asset_id=order.asset_id, symbol=order.symbol,
                                    limit_price=float(order.limit_price),
                                    order_type=order.order_type, side=order.side, qty=int(order.qty),
                                    filled_qty=int(order.filled_qty), time_in_force=order.time_in_force,
                                    status=order.status)

        if not position_exists:
            print("Position Liquidated")
            trades_stream.positions.remove(position)
            hedging = False

        time.sleep(10.0)


# This block of code is the catalyst to running our algorithm and stock market checks
if __name__ == '__main__':
    main()
