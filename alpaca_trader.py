import alpaca_trade_api as tradeapi
import requests
import json
import time
import socket
from datetime import date, timedelta

# Alpaca api
api = tradeapi.REST(
    key_id='PKTC3DTGK63X5OTVOZVS',
    secret_key='ii/nXagoCRvz2GWFncyId1F/gJCvukrMI1q/vkjg',
    base_url='https://paper-api.alpaca.markets'
)


# market clock
def market_clock():
    clock = api.get_clock()
    print ('The market is {}'.format('open.' if clock.is_open else 'closed.'))
    if clock.is_open:
        return True
    else:
        return False


# find out how to use sockets
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


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
    sell_spread = bid(expensive_class) - ask(cheaper_class)

    return sell_spread


# spread calculator based off bid and ask DEBT
def debit_spread_calc(cheaper_class, expensive_class):
    buy_spread = ask(expensive_class) - bid(cheaper_class)

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


# sends orders based on bid/ask using limits needs work (we need to find out how to cancel orders) and error handling
def lim_order_placer(cheaper_class, expensive_class, sell_spread_price, buy_spread_price, qty_e, qty_c, position):
    if position == 'sell':
        while True:
            print(credit_spread_calc(cheaper_class, expensive_class))
            if credit_spread_calc(cheaper_class, expensive_class) > sell_spread_price:
                print(round((spread_calc(cheaper_class, expensive_class)), 2))
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
            print(credit_spread_calc(cheaper_class, expensive_class))
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


lim_order_placer('GOOG', 'GOOGL', .26, 1, 1, 'sell')


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

        if spread_calc(cheaper_class, expensive_class) > sell_spread_price:
            print(round((spread_calc(cheaper_class, expensive_class)), 2))
            sell_order(expensive_class, qty_e)
            buy_order(cheaper_class, qty_c)
            print('Credit Spread Bought')
            break

        elif spread_calc(cheaper_class, expensive_class) < buy_spread_price - 4:
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


# spread_trader('UA', 'UAA', 2.00, 1.9, 10)
