import websocket
import json
import alpaca_trade_api as alpaca
from alpaca_trade_api import StreamConn
from threading import Thread
from multiprocessing import Process
import time

alpaca_api = alpaca.REST(
    key_id='PKT95IYTT39JEFETIJP7',
    secret_key='xb5O2safuUJnrR5Ox1JZF8pfF6/oEeFUO0k1q8NM',
    base_url='https://paper-api.alpaca.markets',
)

conn = StreamConn(
    key_id="PKT95IYTT39JEFETIJP7",
    secret_key="xb5O2safuUJnrR5Ox1JZF8pfF6/oEeFUO0k1q8NM",
    base_url="https://paper-api.alpaca.markets",
)

goog_data = {
    "sym": "GOOG",
    "p": None,
    "bp": None,
    "ap": None,
}

googl_data = {
    "sym": "GOOGL",
    "p": None,
    "bp": None,
    "ap": None,
}

account = {
    "buyingPower": None,
    "portfolioValue": None,
    "regTBuyingPower": None,
}

positions = []

orders = []


# Alpaca has not made account updates useful yet
'''@conn.on(r'account_updates')
async def on_account_updates(conn, channel, account):
    print('account', account)'''


@conn.on(r'trade_updates')
async def on_trade_updates(conn, channel, data):

    global orders

    order_data = data
    order = order_data.order
    packaged_order = {
            "id": order["id"],
            "symbol": order["symbol"],
            "limitPrice": order["limit_price"],
            "orderType": order["order_type"],
            "qty": order["qty"],
            "filled_qty": order["filled_qty"],
            "side": order["side"],
            "timeInForce": order["time_in_force"],
            "status": order["status"],
        }

    if order_data.event == "new":
        orders.append(packaged_order)
    elif order_data.event == "fill":
        orders = [ordr for ordr in orders if ordr["id"] != packaged_order["id"]]
    elif order_data.event == "partial_fill":
        orders = [ordr for ordr in orders if ordr["id"] != packaged_order["id"]]
        orders.append(packaged_order)
    elif order_data.event == "canceled" or order_data.event == "expired":
        orders = [ordr for ordr in orders if ordr["id"] != packaged_order["id"]]


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
        # Run Stream Connection Functions
        Thread(target=stock_data_updates).start()
        Thread(target=account_updates).start()
        Thread(target=position_updates).start()
        Thread(target=order_updates).start()
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


def order_updates():
    conn.run(['trade_updates'])


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
                positions = positions

        except Exception as error:
            print(error)

        time.sleep(0.5)
        print(positions)


def stock_data_updates():
    print('Started Running')

    # Subscribes WebSocket to stocks
    ws = websocket.WebSocketApp("wss://alpaca.socket.polygon.io/stocks", on_message=on_message, on_open=on_open,
                                on_close=on_close, on_error=on_error)

    ws.on_open = on_open
    ws.run_forever()


def on_message(ws, message):
    stock_data = json.loads(message)

    global goog_data
    global googl_data

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
    stock_data_exists = check_stock_data()

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

        spread = expensive_class["p"] - (cheaper_class["p"] * ratio)

        if spread > 1.25:
            filtered_positions = list(
                filter(lambda position: (position["symbol"] == expensive_class["sym"] and int(position["qty"]) < 0), positions))
            filtered_orders = list(
                filter(lambda order: (order["sym"] == expensive_class["sym"] and int(order["side"]) == "sell"), orders))
            if len(filtered_positions) < 1 and len(filtered_orders):
                open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='credit', ratio=ratio)
        elif spread < 0.75:
            filtered_positions = list(
                filter(lambda position: (position["symbol"] == expensive_class["sym"] and int(position["qty"]) < 0),
                       positions))
            filtered_orders = list(
                filter(lambda order: (order["sym"] == expensive_class["sym"] and int(order["side"]) == "buy"), orders))
            if len(filtered_positions) < 1 and len(filtered_orders) < 1:
                open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='debit', ratio=ratio)


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


def open_position(expensive_class, cheaper_class, side, ratio):
    # Figure out how to stop the program from opening too many positions
    try:
        if side == "credit":
            if account["buyingPower"] >= cheaper_class["ap"]:  # Ask Drew what the cost of the trade is
                alpaca_api.submit_order(expensive_class["sym"], qty=1, side='sell', type='limit', limit_price=expensive_class["ap"], time_in_force='gtc')
                alpaca_api.submit_order(cheaper_class["sym"], qty=int(ratio), side='buy', type='limit', limit_price=cheaper_class["bp"], time_in_force='gtc')
                print('Credit Spread Bought')
        elif side == "debit":
            if account["buyingPower"] >= expensive_class["ap"]:  # Ask Drew what the cost of the trade is
                alpaca_api.submit_order(cheaper_class["sym"], qty=int(ratio), side='sell', type='limit', limit_price=cheaper_class["ap"], time_in_force='gtc')
                alpaca_api.submit_order(expensive_class["sym"], qty=1, side='buy', type='limit', limit_price=expensive_class["bp"], time_in_force='gtc')
                print('Debit Spread Bought')
    except Exception as error:
        print(error)


def close_position(expensive_class, cheaper_class, side, ratio):
    print("CLOSE POSITION")
    if side == "credit":
        if account["buyingPower"] >= (cheaper_class["ap"] * ratio):  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(expensive_class, qty=1, side='sell', type='limit', limit_price=expensive_class["bp"], time_in_force='gtc')
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='buy', type='limit', limit_price=cheaper_class["ap"], time_in_force='gtc')
            print('Debit Spread Closed')
    elif side == "debit":
        if account["buyingPower"] >= expensive_class["ap"]:  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='sell', type='limit', limit_price=cheaper_class["ap"], time_in_force='gtc')
            alpaca_api.submit_order(expensive_class, qty=1, side='buy', type='limit', limit_price=expensive_class["bp"], time_in_force='gtc')
            print('Credit Spread Closed')


if __name__ == '__main__':
    main()
