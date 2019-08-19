import websocket
import json
import alpaca_trade_api as alpaca
from alpaca_trade_api import StreamConn
from threading import Thread
from multiprocessing import Process

alpaca_api = alpaca.REST(
    key_id='PKK6KCNM8934NJW6JNUG',
    secret_key='alXAfxljGTWkSOyeCONFQvXAxdWhKbDL8fmRgH7H',
    base_url='https://paper-api.alpaca.markets',
)

conn = StreamConn(
    key_id="PKK6KCNM8934NJW6JNUG",
    secret_key="alXAfxljGTWkSOyeCONFQvXAxdWhKbDL8fmRgH7H",
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
    "RegTBuyingPower": None,
}

positions = {}

orders = []


@conn.on(r'.*')
async def on_data(conn, channel, data):
    print(channel)
    print(data)


@conn.on(r'^account_updates$')
async def on_account_updates(conn, channel, account):
    print('account', account)


@conn.on(r'^trade_updates$')
async def on_trade_updates(conn, channel, data):
    print(data)


def main():
    global positions
    global orders

    # Retrieves initial account data before running algorithm
    # TODO: add a function that retrieves the historical data of GOOG and GOOGL
    positions = get_positions()
    orders = get_orders()

    if positions is not None or orders is not None:
        # Run Algorithm Here
        Thread(target=stock_data_update).start()
        Thread(target=account_updates).start()
    else:
        print("Error Occurred: Either a failure in fetching account positions or orders")


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
    conn.run(['account_updates', 'trade_updates'])


def stock_data_update():
    print('Started Running')

    # Subscribes WebSocket to stocks
    ws = websocket.WebSocketApp("wss://alpaca.socket.polygon.io/stocks", on_message=on_message, on_open=on_open,
                                on_close=on_close, on_error=on_error)

    ws.on_open = on_open
    ws.run_forever()

    '''while True:
        # clock API returns the server time including
        # the boolean flag for market open
        clock = alpaca_api.get_clock()
        now = clock.timestamp
        print(stock_data)
        if clock.is_open:
            print(stock_data)'''


def on_data(conn, channel, data):
    print(data)


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
            open_position(expensive_class=expensive_class, cheaper_class=cheaper_class, side='credit', ratio=ratio)
        elif spread < 0.75:
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
    if side == "credit":
        if account["buyingPower"] >= cheaper_class["ap"]:  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(expensive_class, qty=1, side='sell', type='limit', limit_price=expensive_class["bp"], time_in_force='gtc')
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='buy', type='limit', limit_price=cheaper_class["ap"], time_in_force='gtc')
            print('Credit Spread Bought')
    elif side == "debit":
        if account["buyingPower"] >= expensive_class["ap"]:  # Ask Drew what the cost of the trade is
            alpaca_api.submit_order(cheaper_class, qty=ratio, side='sell', type='limit', limit_price=cheaper_class["ap"], time_in_force='gtc')
            alpaca_api.submit_order(expensive_class, qty=1, side='buy', type='limit', limit_price=expensive_class["bp"], time_in_force='gtc')
            print('Debit Spread Bought')


def close_position():
    print("CLOSE POSITION")


if __name__ == '__main__':
    main()
