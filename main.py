import websocket
import json
import alpaca_trade_api as alpaca
from alpaca_trade_api import StreamConn
from threading import Thread
from models.order import Order
from models.hedged_order import HedgedOrder
from multiprocessing import Process
import time

# Declaration of Alpaca API
alpaca_api = alpaca.REST(
    key_id='PKT95IYTT39JEFETIJP7',
    secret_key='xb5O2safuUJnrR5Ox1JZF8pfF6/oEeFUO0k1q8NM',
    base_url='https://paper-api.alpaca.markets',
)

# Declaration of stream
conn = StreamConn(
    key_id="PKT95IYTT39JEFETIJP7",
    secret_key="xb5O2safuUJnrR5Ox1JZF8pfF6/oEeFUO0k1q8NM",
    base_url="https://paper-api.alpaca.markets",
)

# Declaration of Google Class C data (empty)
goog_data = {
    "sym": "GOOG",
    "p": None,
    "bp": None,
    "ap": None,
}

# Declaration of Google Class A data (empty)
googl_data = {
    "sym": "GOOGL",
    "p": None,
    "bp": None,
    "ap": None,
}

# Declaration of Alpaca account data (empty)
account = {
    "buyingPower": None,
    "portfolioValue": None,
    "regTBuyingPower": None,
}

# Declaration of our positions and orders (empty)
positions = []
orders = []

# Alpaca has not made account updates useful yet
'''@conn.on(r'account_updates')
async def on_account_updates(conn, channel, account):
    print('account', account)'''


# Function that is called whenever an order update occurs (new orders, fills, partial fills, cancels, etc...)
@conn.on(r'trade_updates')
async def on_trade_updates(conn, channel, data):
    global orders

    order_data = data
    order = order_data.order
    packaged_order = Order(order["id"], order["symbol"], order["limit_price"], order["order_type"], order["qty"],
                           order["filled_qty"], order["side"], order["time_in_force"], order["status"])

    if order_data.event == "new":
        orders.append(packaged_order)
        print("Timer Started")
        time.sleep(5.0)
        try:
            print("Time Elapsed 5 Seconds")
            '''for ordr in orders:
                if ordr["id"] == packaged_order["id"]:
                    alpaca_api.cancel_order(
                        packaged_order["id"])  # Cancels order if it still hasn't executed after 2 secs
                    orders.remove(ordr)
                    if len(positions) % 2 == 0:
                        alpaca_api.close_all_positions()
                    if packaged_order["side"] == "buy":
                        print("Bid Increased")
                    elif packaged_order["side"] == "sell":
                        print("Ask Increased")'''
        except Exception as error:
            print(error)
    elif order_data.event == "fill":
        orders = [ordr for ordr in orders if ordr.id != packaged_order.id]
    elif order_data.event == "partial_fill":
        orders = [ordr for ordr in orders if ordr.id != packaged_order.id]
        orders.append(packaged_order)
    elif order_data.event == "canceled" or order_data.event == "expired":
        orders = [ordr for ordr in orders if ordr["id"] != packaged_order.id]


def main():
    # Local versions of our account data, current positions, and awaiting orders
    global account
    global positions
    global orders

    # Retrieves initial account data before running algorithm
    # TODO: add a function that retrieves the historical data of GOOG and GOOGL
    account = get_account()
    positions = get_positions()
    orders = get_orders()

    if account is not None and positions is not None and orders is not None:
        # Runs stream connection functions in different threads
        Thread(target=stock_data_updates).start()
        Thread(target=account_updates).start()
        Thread(target=position_updates).start()
        Thread(target=conn.run(['trade_updates'])).start()
    else:
        print("Error Occurred: Either a failure in fetching account data, positions, or orders")


def get_account():
    try:
        account_info = alpaca_api.get_account()
        account = {
            "buyingPower": float(account_info.buying_power),
            "portfolioValue": float(account_info.portfolio_value),
            "regTBuyingPower": float(account_info.regt_buying_power),
        }
        return account
    except Exception as error:
        print(error)
        return None


def get_positions():
    positions = []

    try:
        position_list = alpaca_api.list_positions()
        if len(position_list) != 0:
            for position in position_list:
                positions.append({
                    "symbol": position.symbol,
                    "qty": position.qty,
                    "side": position.side,
                    "marketValue": position.market_value,
                    "currentPrice": position.current_price,
                })
        return positions
    except Exception as error:
        print(error)
        return None


def get_orders():
    orders = []

    try:
        order_list = alpaca_api.list_orders()
        if len(order_list) != 0:
            filtered_order_list = list(
                filter(lambda o: o.canceled_at is None and o.filled_at is None and o.failed_at is None, order_list))
            if len(filtered_order_list) != 0:
                for order in filtered_order_list:
                    orders.append({
                        "id": order.id,
                        "symbol": order.symbol,
                        "limitPrice": order.limit_price,
                        "orderType": order.order_type,
                        "qty": order.qty,
                        "side": order.side,
                        "timeInForce": order.time_in_force,
                        "status": order.status,
                    })
        return orders
    except Exception as error:
        print(error)
        return None


def account_updates():
    global account

    while True:
        try:
            account_info = alpaca_api.get_account()
            account = {
                "buyingPower": float(account_info.buying_power),
                "portfolioValue": float(account_info.portfolio_value),
                "regTBuyingPower": float(account_info.regt_buying_power),
            }
        except Exception as error:
            print(error)
        time.sleep(0.5)


def position_updates():
    global positions

    current_positions = []

    while True:
        try:
            position_list = alpaca_api.list_positions()
            if len(position_list) != 0:
                for position in position_list:
                    current_positions.append({
                        "symbol": position.symbol,
                        "qty": position.qty,
                        "side": position.side,
                        "marketValue": position.market_value,
                        "currentPrice": position.current_price,
                    })
                positions = current_positions
            else:
                positions = []

        except Exception as error:
            print(error)

        time.sleep(0.5)


def stock_data_updates():
    print('Started Running')

    # Subscribes WebSocket to stocks
    ws = websocket.WebSocketApp("wss://alpaca.socket.polygon.io/stocks", on_message=on_message, on_open=on_open,
                                on_close=on_close, on_error=on_error)

    ws.on_open = on_open
    ws.run_forever()


# Function that gets called whenever the stocks bid price, ask price, or share price changes
def on_message(ws, message):
    stock_data = json.loads(message)

    global goog_data
    global googl_data

    # Filters out stock's trade info (last trade)
    if stock_data[0]["ev"] == 'T':
        goog_trade = next((stock for stock in stock_data if stock["sym"] == "GOOG"), goog_data)
        if goog_trade["p"] is not None and goog_trade["p"] is not None:
            goog_data["p"] = goog_trade["p"]
            goog_data["p"] = goog_trade["p"]
            # print(goog_data)
        googl_trade = next((stock for stock in stock_data if stock["sym"] == "GOOGL"), googl_data)
        if googl_trade["p"] is not None and googl_trade["p"] is not None:
            googl_data["p"] = googl_trade["p"]
            googl_data["p"] = googl_trade["p"]

    # Filters out stock's quote (current bid and ask price)
    if stock_data[0]["ev"] == 'Q':
        goog_quote = next((stock for stock in stock_data if stock["sym"] == "GOOG"), goog_data)
        if goog_quote["bp"] is not None and goog_quote["ap"] is not None:
            goog_data["bp"] = goog_quote["bp"]
            goog_data["ap"] = goog_quote["ap"]
            # print(goog_data)
        googl_quote = next((stock for stock in stock_data if stock["sym"] == "GOOGL"), googl_data)
        if googl_quote["bp"] is not None and googl_quote["ap"] is not None:
            googl_data["bp"] = googl_quote["bp"]
            googl_data["ap"] = googl_quote["ap"]

    market_is_open = True
    stock_data_exists = True

    if market_is_open and stock_data_exists:
        # Run Algorithm Here

        expensive_class = None
        cheaper_class = None
        ratio = 1 / 1
        if goog_data["p"] >= googl_data["p"]:
            expensive_class = goog_data
            cheaper_class = googl_data
        else:
            expensive_class = googl_data
            cheaper_class = goog_data

        credit_spread = expensive_class["ap"] - (cheaper_class["bp"] * ratio)
        debit_spread = expensive_class["bp"] - (cheaper_class["ap"] * ratio)

        if credit_spread > 1.50:

            position_exists = check_positions(expensive_class=expensive_class, side="credit")
            order_exists = check_orders(expensive_class=expensive_class, side="credit")
            print(f'Position Exists: {position_exists}')
            print(f'Order Exists: {order_exists}')

            if not order_exists and not position_exists:

                open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='credit', ratio=ratio)

            elif position_exists and not order_exists:

                for position in positions:
                    if position["symbol"] == expensive_class["sym"] and position["side"] == "short":
                        open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='credit',
                                      ratio=ratio)

        elif debit_spread < 0.50:

            position_exists = check_positions(expensive_class=expensive_class, side="debit")
            order_exists = check_orders(expensive_class=expensive_class, side="debit")

            if not order_exists and not position_exists:

                open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='debit', ratio=ratio)

            elif position_exists and not order_exists:
                for position in positions:
                    if position["symbol"] == expensive_class["sym"] and position["side"] == "long":
                        open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='debit',
                                      ratio=ratio)


def on_error(ws, error):
    # ws.send('{"action":"unsubscribe","params":"Q.GOOG, Q.GOOGL"}')
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send('{"action":"auth","params":"AKK5WUTECIGM1G8XTN3C"}')
    ws.send('{"action":"subscribe","params":"Q.GOOG,T.GOOG,Q.GOOGL,T.GOOGL"}')


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
    if goog_data["p"] is not None and goog_data["bp"] is not None and goog_data["ap"] is not None and googl_data[
        "p"] is not None and googl_data["bp"] is not None and googl_data["ap"] is not None:
        return True
    else:
        return False


def check_positions(expensive_class, side):
    if len(positions) >= 1:
        return True
        '''if side == "credit":
            for position in positions:
                position_exists = None
                if position["symbol"] == expensive_class["sym"] and position["side"] == "short":
                    position_exists = True
                else:
                    position_exists = False
            return position_exists
        elif side == "debit":
            for position in positions:
                position_exists = None
                if position["symbol"] == expensive_class["sym"] and position["side"] == "long":
                    position_exists = True
                else:
                    position_exists = False
            return position_exists'''
    else:
        return False


def check_orders(expensive_class, side):
    if len(orders) >= 1:
        return True
        '''if side == "credit":
            order_exists = None
            for order in orders:
                if order["symbol"] == expensive_class["sym"] and order["side"] == "sell":
                    order_exists = True
                else:
                    order_exists = False
            return order_exists
        elif side == "debit":
            order_exists = None
            for order in orders:
                if order["symbol"] == expensive_class["sym"] and order["side"] == "buy":
                    order_exists = True
                else:
                    order_exists = False
            return order_exists'''
    else:
        return False


def open_position(expensive_class, cheaper_class, side, ratio):
    # Figure out how to stop the program from opening too many positions
    try:
        if side == "credit":
            if account["buyingPower"] >= cheaper_class["ap"] + expensive_class["bp"]:
                alpaca_api.submit_order(expensive_class["sym"], qty=1, side='sell', type='limit',
                                        limit_price=expensive_class["ap"] - .60, time_in_force='gtc')
                alpaca_api.submit_order(cheaper_class["sym"], qty=int(ratio), side='buy', type='limit',
                                        limit_price=cheaper_class["bp"] + .60, time_in_force='gtc')
                print('Credit Spread Bought')
        elif side == "debit":
            if account["buyingPower"] >= expensive_class["ap"] + cheaper_class["bp"]:
                alpaca_api.submit_order(cheaper_class["sym"], qty=int(ratio), side='sell', type='limit',
                                        limit_price=cheaper_class["ap"] - .60, time_in_force='gtc')
                alpaca_api.submit_order(expensive_class["sym"], qty=1, side='buy', type='limit',
                                        limit_price=expensive_class["bp"] + .60, time_in_force='gtc')
                print('Debit Spread Bought')
    except Exception as error:
        print(error)


def close_position(expensive_class, cheaper_class, side, ratio):
    print("CLOSE POSITION")
    if side == "credit":
        if account["buyingPower"] >= (cheaper_class["ap"] * ratio):  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(expensive_class, qty=1, side='sell', type='limit',
                                    limit_price=expensive_class["bp"], time_in_force='gtc')
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='buy', type='limit', limit_price=cheaper_class["ap"],
                                    time_in_force='gtc')
            print('Debit Spread Closed')
    elif side == "debit":
        if account["buyingPower"] >= expensive_class["ap"]:  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='sell', type='limit',
                                    limit_price=cheaper_class["ap"], time_in_force='gtc')
            alpaca_api.submit_order(expensive_class, qty=1, side='buy', type='limit', limit_price=expensive_class["bp"],
                                    time_in_force='gtc')
            print('Credit Spread Closed')


# This block of code is the catalyst to running our algorithm and stock market checks
if __name__ == '__main__':
    main()
