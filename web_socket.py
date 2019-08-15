import websocket
import json

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

if __name__ == '__main__':
    main()