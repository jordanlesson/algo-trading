import alpaca_trade_api as tradeapi
import requests
import json
import time

# alpca api
api = tradeapi.REST(
    key_id='PKD460RLG1G4D7LFKGZ5',
    secret_key='qYVDQVKe//lu4SOVc29tJpFCWw6v4SWQthKVPYZv',
    base_url='https://paper-api.alpaca.markets'
)



#market clock
def market_clock():
    clock = api.get_clock()
    print('The market is {}'.format('open.' if clock.is_open else 'closed.'))


# our buying power
def buying_power():
    account = api.get_account()
    print(('${} buying power'.format(account.buying_power)))

# order template
def order(symbol, quantity, postion):
    api.submit_order(symbol=str(symbol),
    qty=quantity,
    side=postion,
    type='market',
    time_in_force='gtc')


# Polygon Price finder
def price(ticker):
    polygon = 'https://api.polygon.io/v1/last/stocks/{}?apiKey=AKK5WUTECIGM1G8XTN3C'.format(ticker)
    res = requests.get(polygon)
    y = json.loads(res.text)
    price = y['last']['price']
    return price


print(price('TSLA'))


# IEX ask finder
def ask(ticker):
    iex = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_04eef91991b64fd5a484b044a2f8a3b1'.format(ticker)
    res = requests.get(iex)
    y = json.loads(res.text)
    price = y['iexAskPrice']

    return price


# IEX bid finder
def bid(ticker):
    iex = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_04eef91991b64fd5a484b044a2f8a3b1'.format(ticker)
    res = requests.get(iex)
    y = json.loads(res.text)
    price = y['iexBidPrice']

    return price


# spread calculator based off bid and ask
def buy_spread_calc(class_a, class_b):
    buy_spread = ask(class_b) - bid(class_a)

    return buy_spread


# spread calculator based of price
def spread_calc(class_a, class_b):
    buy_spread = price(class_b) - price(class_a)

    return buy_spread


#sell short cut for market orders
def sell_order(classab, qty):
    order(classab, qty, 'sell')


#buy short cut for market orders
def buy_order(classab, qty):
    order(classab, qty, 'buy')


first_trade = True

goog_position = api.get_position('GOOG')


if api.get_position('GOOGL').qty == 12:
    print('shalom')

def bell_trader(class_a, class_b, sell_spread_price, buy_spread_price, qty):
    while first_trade:

        if spread_calc(class_a, class_b) > sell_spread_price:
            print(spread_calc(class_a, class_b))
            sell_order(class_b, qty)
            buy_order(class_a, qty)

        elif spread_calc(class_a, class_b) < buy_spread_price:
            print(spread_calc(class_a, class_b))
            sell_order(class_a, qty)
            buy_order(class_b, qty)
        else:
            print(spread_calc(class_a, class_b))

        if api.get_position(class_a).qty == qty:
            break
    time.sleep(1)


bell_trader('GOOG', 'GOOGL', 2.65, .6, 3)

print(api.get_position('GOOGL').qty)


if api.get_position('GOOGL').qty == 12:
    print('shalom')
