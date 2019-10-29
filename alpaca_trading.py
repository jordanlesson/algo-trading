import alpaca_trade_api as alpaca
import requests
import json
import time
import websocket
import asyncio

alpaca_api = alpaca.REST(
    key_id='PKTC3DTGK63X5OTVOZVS',
    secret_key='ii/nXagoCRvz2GWFncyId1F/gJCvukrMI1q/vkjg',
    base_url='https://paper-api.alpaca.markets'
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

    alpaca_api.

    # Creates WebSocket
    ws = websocket.WebSocketApp("wss://alpaca.socket.polygon.io/stocks", on_message=on_message, on_open=on_open,
                                on_close=on_close, on_error=on_error)
    ws.run_forever()


# Calls anytime GOOG's or GOOGL's price, ask price, or bid price changes
def on_message(ws, message):
    print(message)
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

        spread_trader()


def on_open(ws):
    ws.send('{"action":"auth","params":"AKK5WUTECIGM1G8XTN3C"}')
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



def spread_trader(cheaper_class, expensive_class, spread, sell_spread_price, buy_spread_price, qty_e, qty_c):
    open_position(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)
    time.sleep(7)
    close_position(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)


def open_position(cheaper_class, expensive_class, spread, sell_spread_price, buy_spread_price, qty_e, qty_c):
    while True:

        if spread > sell_spread_price:
            alpaca_api.submit_order(expensive_class, qty=qty_e, side='sell', type='market', time_in_force='gtc')
            alpaca_api.submit_order(cheaper_class, qty=qty_c, side='buy', type='market', time_in_force='gtc')
            print('Credit Spread Bought')
            break

        elif spread(cheaper_class, expensive_class) < buy_spread_price - 4:
            alpaca_api.submit_order(cheaper_class, qty=qty_c, side='sell', type='market', time_in_force='gtc')
            alpaca_api.submit_order(expensive_class, qty=qty_e, side='buy', type='market', time_in_force='gtc')
            print('Debit Spread Bought')
            break

        else:
            print('No Spread Bought')

        time.sleep(.3)


def close_position(cheaper_class, expensive_class, spread, sell_spread_price, buy_spread_price, qty_e, qty_c):

    if (int(alpaca_api.get_position(expensive_class).qty)) > 0:
        print('Credit found')
        while True:
            print()
            print('no spread bought')
            if spread > sell_spread_price:
                alpaca_api.submit_order(expensive_class, qty=qty_e, side='sell', type='market', time_in_force='gtc')
                alpaca_api.submit_order(cheaper_class, qty=qty_c, side='buy', type='market', time_in_force='gtc')
                print('Credit Spread Bought')
                print('no open positions should exist')
                break
            time.sleep(.4)

    elif (int(alpaca_api.get_position(cheaper_class).qty)) > 0:
        print('Debit found')
        while True:
            print('no spread bought')
            if spread < buy_spread_price:
                alpaca_api.submit_order(cheaper_class, qty=qty_c, side='sell', type='market', time_in_force='gtc')
                alpaca_api.submit_order(expensive_class, qty=qty_e, side='buy', type='market', time_in_force='gtc')
                print('Debit Spread Bought')
                print('no open positions should exist')
                break
            time.sleep(.4)

        else:
            print('ERROR NO SPREAD FOUND')


# sends orders based on bid/ask using limits needs work (we need to find out how to cancel orders) and error handling
def lim_order_placer(cheaper_class, expensive_class, spread, bid_price, ask_price sell_spread_price, buy_spread_price, qty_e, qty_c, position):
    if position == 'sell':
        while True:
            if credit_spread_calc(cheaper_class, expensive_class) > sell_spread_price:
                lim_e = bid(expensive_class)
                lim_order(expensive_class, qty_e, 'sell', lim_e)
                lim_c = ask(cheaper_class)
                lim_order(cheaper_class, qty_c, 'buy', lim_c)
                try:
                    if int(api.get_position(expensive_class).qty) != 1:
                        lim_e = bid(expensive_class)*.9
                        lim_order(expensive_class, qty_e, 'sell', lim_e)
                except Exception as e:
                    lim_e = bid(expensive_class) * .9
                    lim_order(expensive_class, qty_e, 'sell', lim_e)
                try:
                    if int(api.get_position(cheaper_class).qty) != 1:
                        lim_e = ask(cheaper_class)*1.1
                        lim_order(cheaper_class, qty_e, 'buy', lim_e)
                except Exception as e:
                    if int(api.get_position(cheaper_class).qty) != 1:
                        lim_e = ask(cheaper_class) * 1.1
                        lim_order(cheaper_class, qty_e, 'buy', lim_e)
                print('Credit Spread Bought CHECK ORDER BOOK')
                break
    if position == 'buy':
        while True:
            if credit_spread_calc(cheaper_class, expensive_class) < buy_spread_price:
                print(round((spread_calc(cheaper_class, expensive_class)), 2))
                lim_e = ask(expensive_class)
                lim_order(expensive_class, qty_e, 'buy', lim_e)
                lim_c = bid(cheaper_class)
                lim_order(cheaper_class, qty_c, 'sell', lim_c)
                try:
                    if int(api.get_position(expensive_class).qty) != 1:
                        lim_c = bid(expensive_class)*.96
                        lim_order(expensive_class, qty_c, 'sell', lim_c)
                except Exception as e:
                    lim_e = bid(expensive_class) * .96
                    lim_order(expensive_class, qty_e, 'sell', lim_e)
                try:
                    if int(api.get_position(cheaper_class).qty) != 1:
                        lim_e = ask(cheaper_class)*1.04
                        lim_order(cheaper_class, qty_e, 'buy', lim_e)
                except Exception as e:
                    if int(api.get_position(cheaper_class).qty) != 1:
                        lim_e = ask(cheaper_class) * 1.04
                        lim_order(cheaper_class, qty_e, 'buy', lim_e)

                print('Credit Spread Bought')
                break


# def open_position(cheaper_stock, expensive_stock, spread, ):


# def close_position():


if __name__ == "__main__":
    main()
