import alpaca_trade_api as tradeapi
import requests
import json
import time
from datetime import date, timedelta
import websocket

api = tradeapi.REST(
    key_id='PKZXCTOAQZQZGJ0A1FCX',
    secret_key='1AZA7ZUXo9X82xg9IeBOFtExwbvb5DZcmoIxHUt1',
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
        #print(spread)
        # open_position()
        # close_position()


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
        clock = api.get_clock()
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


#if __name__ == "__main__":
#    main()

#main()

# market clock
def market_clock():
    clock = api.get_clock()
    print ('The market is {}'.format('open.' if clock.is_open else 'closed.'))
    if clock.is_open:
        return True
    else:
        return False

# our buying power
def buying_power():
    account = api.get_account()
    print(('${} buying power'.format(account.buying_power)))


# order template gtc = good till cancel
def order(symbol, quantity, postion):
    api.submit_order(symbol=str(symbol), qty=quantity, side=postion, type='market', time_in_force='gtc'
                     )


def lim_order(symbol, quantity, postion, lim):
    api.submit_order(symbol=str(symbol),
    qty=quantity,
    side=postion,
    type='limit',
    time_in_force='gtc',
    limit_price=lim)


# Polygon Price finder
def price(ticker):
    polygon = 'https://api.polygon.io/v1/last/stocks/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(ticker)
    res = requests.get(polygon)
    y = json.loads(res.text)
    price = y['last']['price']

    return price


# polygon ask finder
def ask(ticker):
    polygon = 'https://api.polygon.io/v1/last_quote/stocks/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(ticker)
    res = requests.get(polygon)
    y = json.loads(res.text)
    ask = y['last']['askprice']

    return ask


# Polygon bid finder
def bid(ticker):
    polygon = 'https://api.polygon.io/v1/last_quote/stocks/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(ticker)
    res = requests.get(polygon)
    y = json.loads(res.text)
    bid = y['last']['bidprice']

    return bid


# spread calculator based off bid and ask CREDIT
def credit_spread_calc(cheaper_class, expensive_class):
    sell_spread = ask(expensive_class) - bid(cheaper_class)

    return sell_spread


# spread calculator based off bid and ask DEBT
def debit_spread_calc(cheaper_class, expensive_class):
    buy_spread = bid(expensive_class) - ask(cheaper_class)

    return buy_spread


# spread calculator based of price
def spread_calc(cheap, expensive):
    buy_spread = price(expensive) - price(cheap)

    return buy_spread


#sell short-cut for market orders
def sell_order(classab, qty):
    order(classab, qty, 'sell')


# buy short-cut for market orders
def buy_order(classab, qty):
    order(classab, qty, 'buy')


def get_historical_data(cheaper_class, expensive_class):

    current_date = date.today()
    past_date = current_date - timedelta(days=28)
    print(past_date)

    cheaper_class_api = 'https://api.polygon.io/v2/aggs/ticker/{}/range/1/day/{}/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(cheaper_class, str(past_date), str(current_date))
    expensive_class_api = 'https://api.polygon.io/v2/aggs/ticker/{}/range/1/day/{}/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(expensive_class, str(past_date), str(current_date))
    cheaper_class_response = requests.get(cheaper_class_api)
    expensive_class_response = requests.get(expensive_class_api)

    cheaper_class_data = json.loads(cheaper_class_response.text)
    expensive_class_data = json.loads(expensive_class_response.text)

    cheaper_class_total_price = 0.0
    expensive_class_total_price = 0.0

    cheaper_class_avg_price = None
    expensive_class_avg_price = None

    cheaper_class_results = cheaper_class_data["results"]
    expensive_class_results = expensive_class_data["results"]

    cheap_result_count = cheaper_class_data["resultsCount"]
    expensive_result_count = expensive_class_data["resultsCount"]

    cheap_index = 0
    expensive_index = 0

    for cheaper_class_stat in cheaper_class_results:
        cheaper_class_total_price = cheaper_class_total_price + float(cheaper_class_stat["c"])

        cheap_index += 1

        if cheap_index == cheap_result_count - 1:
            cheaper_class_avg_price = cheaper_class_total_price / cheap_result_count

    for expensive_class_stat in expensive_class_results:
        expensive_class_total_price = expensive_class_total_price + float(expensive_class_stat["c"])

        expensive_index += 1

        if expensive_index == expensive_result_count - 1:
            expensive_class_avg_price = expensive_class_total_price / expensive_result_count

    return expensive_class_avg_price - cheaper_class_avg_price

# print(get_historical_data('GOOG', 'GOOGL'))


def open_trade(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):
    while True:

        if credit_spread_calc(cheaper_class, expensive_class) > sell_spread_price:
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            sell_order(expensive_class, qty_e)
            buy_order(cheaper_class, qty_c)
            print('Credit Spread Bought')
            break

        elif debit_spread_calc(cheaper_class, expensive_class) < buy_spread_price :
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            sell_order(cheaper_class, qty_c)
            buy_order(expensive_class, qty_e)
            print('Debit Spread Bought')
            break

        else:
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            print('No Spread Bought')

        time.sleep(.3)

    print((str(api.get_position(cheaper_class).qty) + cheaper_class))
    print((str(api.get_position(expensive_class).qty) + expensive_class))


def close_trade(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):

    if (int(api.get_position(expensive_class).qty)) > 0:
        print('Credit found')
        while True:
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            print('no spread bought')
            if spread_calc(cheaper_class, expensive_class) > sell_spread_price:
                print(spread_calc(cheaper_class, expensive_class))
                sell_order(expensive_class, qty_e)
                buy_order(cheaper_class, qty_c)
                print('Credit Spread Bought')
                print('no open positions should exist')
                break
            time.sleep(.4)

    elif (int(api.get_position(cheaper_class).qty)) > 0:
        print('Debit found')
        while True:
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            print('no spread bought')
            if spread_calc(cheaper_class, expensive_class) < buy_spread_price:
                print(debit_spread_calc(cheaper_class, expensive_class))
                sell_order(cheaper_class, qty_c)
                buy_order(expensive_class, qty_e)
                print('Debit Spread Bought')
                print('no open positions should exist')
                break
            time.sleep(.4)

        else:
            print('ERROR NO SPREAD FOUND')


def spread_trader(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):
    while True:
        open_trade(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)
        time.sleep(7)
        close_trade(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)


# sends orders based on bid/ask using limits needs work (we need to find out how to cancel orders) and error handling
def lim_order_placer(cheaper_class, expensive_class, qty_e, qty_c, position):
    if position == 'sell':
        lim_e = ask(expensive_class)
        lim_order(expensive_class, qty_e, 'sell', lim_e)
        lim_c = bid(cheaper_class)
        lim_order(cheaper_class, qty_c, 'buy', lim_c)
        print('Order started')
        try:
            if int(api.get_position(expensive_class).qty) != qty_e:
                api.cancel_all_orders()
                lim_e = ask(expensive_class) - spread_calc(cheaper_class, expensive_class) * .1
                lim_order(expensive_class, (qty_e - api.get_position(expensive_class)).qty, 'sell', lim_e)
        except Exception as e:
            api.cancel_all_orders()
            lim_e = ask(expensive_class) - spread_calc(cheaper_class, expensive_class) * .1
            lim_order(expensive_class, qty_e, 'sell', lim_e)
        try:
            if int(api.get_position(cheaper_class).qty) != qty_c:
                api.cancel_all_orders()
                lim_c = bid(cheaper_class) + spread_calc(cheaper_class, expensive_class) * .1
                lim_order(cheaper_class, (qty_c - api.get_position(expensive_class)).qty, 'buy', lim_c)
        except Exception as e:
            api.cancel_all_orders()
            lim_c = bid(cheaper_class) + spread_calc(cheaper_class, expensive_class) * .1
            lim_order(cheaper_class, qty_c, 'buy', lim_c)
        print('Credit Spread Bought CHECK ORDER BOOK')

    if position == 'buy':
        lim_e = bid(expensive_class)
        lim_order(expensive_class, qty_e, 'buy', lim_e)
        lim_c = ask(cheaper_class)
        lim_order(cheaper_class, qty_c, 'sell', lim_c)
        print('Order started')
        try:
            if int(api.get_position(expensive_class).qty) != qty_e:
                api.cancel_all_orders()
                lim_e = bid(expensive_class) + spread_calc(cheaper_class, expensive_class) * .1
                lim_order(expensive_class, (qty_e - api.get_position(expensive_class)).qty, 'buy', lim_e)
        except Exception as e:
            api.cancel_all_orders()
            lim_e = bid(expensive_class) + spread_calc(cheaper_class, expensive_class) * .1
            lim_order(expensive_class, qty_e, 'buy', lim_e)
        try:
            if int(api.get_position(cheaper_class).qty) != qty_c:
                api.cancel_all_orders()
                lim_c = ask(cheaper_class) - spread_calc(cheaper_class, expensive_class) * .1
                lim_order(cheaper_class, (qty_c - api.get_position(expensive_class)).qty, 'sell', lim_c)
        except Exception as e:
            api.cancel_all_orders()
            lim_c = ask(cheaper_class) - spread_calc(cheaper_class, expensive_class) * .1
            lim_order(cheaper_class, qty_c, 'sell', lim_c)
        print('Debit Spread Bought CHECK ORDER BOOK')


def open_trader_lim(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):
    while True:
        if credit_spread_calc(cheaper_class, expensive_class) > sell_spread_price:
            lim_order_placer(cheaper_class,expensive_class, qty_e, qty_c, 'sell')
            break

        elif debit_spread_calc(cheaper_class, expensive_class) < buy_spread_price:
            lim_order_placer(cheaper_class, expensive_class, qty_e, qty_c, 'buy')
            break

        else:
            print('credit spread:' + credit_spread_calc(cheaper_class, expensive_class), 'debit spread:' +
                  debit_spread_calc(cheaper_class, expensive_class))


def close_trader_lim(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):
    if (int(api.get_position(expensive_class).qty)) > 0:
        while True:
            print(round((credit_spread_calc(cheaper_class, expensive_class)), 2))
            print('no spread bought')
            if credit_spread_calc(cheaper_class, expensive_class) > sell_spread_price:
                lim_order_placer(cheaper_class, expensive_class, qty_e, qty_c, 'sell')
                break

    elif (int(api.get_position(cheaper_class).qty)) > 0:
        while True:
            print(round((debit_spread_calc(cheaper_class, expensive_class)), 2))
            print('no spread bought')
            if debit_spread_calc(cheaper_class, expensive_class) < buy_spread_price:
                lim_order_placer(cheaper_class, expensive_class, qty_e, qty_c, 'buy')
                break


def limit_spread_trader(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c):
    while True:
        open_trader_lim(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)
        time.sleep(7)
        close_trader_lim(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c)




limit_spread_trader('GOOG', 'GOOGL', 1.5, 0.3, 1, 1)
#spread_trader('LEN.B','LEN', 10.2, 9.8, 4, 3)
#need websocket

