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

    # Subscribes WebSocket to stocks
    ws = websocket.WebSocketApp("wss://socket.polygon.io/stocks", on_message=on_message, on_error=on_error,
                                on_open=on_open,
                                on_close=on_close)

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


def on_message(ws, message):
    stock_data = json.loads(message)

    global goog_data
    global googl_data

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

        


def on_error(ws, error):
    # ws.send('{"action":"unsubscribe","params":"Q.GOOG, Q.GOOGL"}')
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send('{"action":"auth","params":"ww_5fIE3P_S3jjhoYGqepjlsO5Dek0wER2sgDS"}')
    ws.send('{"action":"subscribe","params":"Q.GOOG,T.GOOG,Q.GOOGL,T.GOOGL"}')


async def get_spread(class_a, class_b):
    try:

        class_a_api = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(
            class_a)
        class_b_api = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(
            class_b)

        class_a_response = requests.get(class_a_api)
        class_b_response = requests.get(class_b_api)

        if class_a_response.status_code == 200 and class_b_response.status_code == 200:

            class_a_data = json.loads(class_a_response.text)

            class_b_data = json.loads(class_b_response.text)

            class_a_info = {
                "symbol": class_a_data["symbol"],
                "latestPrice": class_a_data["latestPrice"],
                "bid": class_a_data["iexBidPrice"],
                "ask": class_a_data["iexAskPrice"],
            }

            class_b_info = {
                "symbol": class_b_data["symbol"],
                "latestPrice": class_b_data["latestPrice"],
                "bid": class_b_data["iexBidPrice"],
                "ask": class_b_data["iexAskPrice"],
            }

            # print(f'{class_a}: {class_a_price}')
            # print(f'{class_b}: {class_b_price}')
            # print(f'Spread: {abs(class_a_price - class_b_price)}')
            return [class_a_info, class_b_info]

        else:

            print("Error Retrieving Stock Price")
            return None

    except IOError:

        print(IOError)
        return None


async def get_historical_data(class_a, class_b):
    try:

        class_a_avg = 'https://cloud.iexapis.com/stable/stock/{}/stats/day200MovingAvg/?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(
            class_a)
        class_b_avg = 'https://cloud.iexapis.com/stable/stock/{}/stats/day200MovingAvg/?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(
            class_b)

        class_a_response = requests.get(class_a_avg)
        class_b_response = requests.get(class_b_avg)

        if class_a_response.status_code == 200 and class_b_response.status_code == 200:

            class_a_data = json.loads(class_a_response.text)
            class_b_data = json.loads(class_b_response.text)

            class_a_avg_price = float(class_a_data)
            class_b_avg_price = float(class_b_data)

            avg_spread = class_a_avg_price - class_b_avg_price

            return avg_spread

        else:

            print('Error Retrieving Average Spread')
            return None

    except IOError:

        print(IOError)
        return None


async def hedge_position(buy_stock, short_stock):
    try:
        account = alpaca_api.get_account()
        positions = alpaca_api.list_positions()
        print(positions)
        if buy_stock["latestPrice"] < float(account.cash):
            alpaca_api.submit_order(short_stock["symbol"], 5, 'sell', 'market', 'day')
            alpaca_api.submit_order(buy_stock["symbol"], 5, 'buy', 'market', 'day')

    except IOError:
        print(IOError)


if __name__ == "__main__":
    main()
