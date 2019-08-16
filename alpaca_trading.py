import alpaca_trade_api as alpaca
import requests
import json
import time
import websocket
import asyncio

alpaca_api = alpaca.REST(
    key_id='PKYGK3F5QQ3NX7LIZKTP',
    secret_key='bpaI7jMkLu1Knnocaz8fzWMBxRC8oxGIqnXGZSk0',
    base_url='https://paper-api.alpaca.markets',
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

def main():
    print('Started Running')

    # Creates WebSocket
    ws = websocket.WebSocketApp("wss://socket.polygon.io/stocks", on_message=on_message, on_open=on_open,
                                on_close=on_close, on_error=on_error)
    ws.run_forever()


# Calls anytime GOOG's or GOOGL's price, ask price, or bid price changes
def on_message(ws, message):
    stock_data = json.loads(message)

    global goog_data
    global googl_data

    # Checks if message contains data of the last stock trade
    if stock_data[0]["ev"] == 'T':
        goog_trade = next((stock for stock in stock_data if stock["sym"] == "GOOG"), goog_data)
        if goog_trade["p"] is not None and goog_trade["p"] is not None:
            goog_data["p"] = goog_trade["p"]
            goog_data["p"] = goog_trade["p"]
            print(goog_data)

        googl_trade = next((stock for stock in stock_data if stock["sym"] == "GOOGL"), googl_data)
        if googl_trade["p"] is not None and googl_trade["p"] is not None:
            googl_data["p"] = googl_trade["p"]
            googl_data["p"] = googl_trade["p"]
            print(googl_data)

    # Checks if message contains stock quote data (ask price, bid price, etc...)
    if stock_data[0]["ev"] == 'Q':
        goog_quote = next((stock for stock in stock_data if stock["sym"] == "GOOG"), goog_data)
        if goog_quote["bp"] is not None and goog_quote["ap"] is not None:
            goog_data["bp"] = goog_quote["bp"]
            goog_data["ap"] = goog_quote["ap"]
            print(goog_data)

        googl_quote = next((stock for stock in stock_data if stock["sym"] == "GOOGL"), googl_data)
        if googl_quote["bp"] is not None and googl_quote["ap"] is not None:
            googl_data["bp"] = googl_quote["bp"]
            googl_data["ap"] = googl_quote["ap"]
            print(googl_data)

    market_is_open = True
    stock_data_exists = check_stock_data()

    if market_is_open and stock_data_exists:

        # Run algorithm here
        expensive_stock = None
        cheaper_stock = None
        if goog_data["p"] >= googl_data["p"]:
            expensive_stock = goog_data
            cheaper_stock = googl_data
        else:
            expensive_stock = googl_data
            cheaper_stock = goog_data
        spread = expensive_stock["p"] - cheaper_stock["p"]
        ratio = 1 / 1
        # print(spread)
        # open_position()
        # close_position()


def on_open(ws):
    ws.send('{"action":"auth","params":"ww_5fIE3P_S3jjhoYGqepjlsO5Dek0wER2sgDS"}')
    ws.send('{"action":"subscribe","params":"Q.GOOG,T.GOOG,Q.GOOGL,T.GOOGL"}')


def on_close(ws):
    print("### closed ###")


def on_error(ws, error):
    # ws.send('{"action":"unsubscribe","params":"Q.GOOG, Q.GOOGL"}')
    print(error)


# Checks if the status of the market
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


# def open_position(cheaper_stock, expensive_stock, spread, ):


# def close_position():


if __name__ == "__main__":
    main()
