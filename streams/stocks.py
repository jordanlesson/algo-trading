import websocket
import json
from models.stock import Stock

# from main import hedging, spread_trader

# Global Declaration of Stock A data (empty)
stock_a = Stock(symbol="GOOG", price=None, bid_price=None, ask_price=None)

# Global Declaration of Stock B data (empty)
stock_b = Stock(symbol="GOOGL", price=None, bid_price=None, ask_price=None)


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


def on_open(ws):
    ws.send('{"action":"auth","params":"AKIM1SK8IUHH731B4UIV"}')
    ws.send(
        '{"action":"subscribe","params":"Q.GOOG,T.GOOG,Q.GOOGL,T.GOOGL"}')


def on_close(ws):
    print("### closed ###")


def on_error(ws, error):
    # ws.send('{"action":"unsubscribe","params":"Q.GOOG,T.GOOG,Q.GOOGL,T.GOOGL"}')
    print(error)
