import alpaca_trade_api as alpaca
import requests
import json
import time
import asyncio

alpaca_api = alpaca.REST(
    key_id = 'PKYGK3F5QQ3NX7LIZKTP',
    secret_key = 'bpaI7jMkLu1Knnocaz8fzWMBxRC8oxGIqnXGZSk0',
    base_url = 'https://paper-api.alpaca.markets',
)


def main():
    # done = None
    print("Start Running")
    while True:
        clock = alpaca_api.get_clock()
        now = clock.timestamp
        if clock.is_open:
            # Do Algorithm Here
            stock_info = asyncio.run(get_spread('GOOG', 'GOOGL'))

            class_a_info = stock_info[0]
            class_b_info = stock_info[1]

            spread = class_a_info["latestPrice"] - class_b_info["latestPrice"]

            if spread is not None:
                average_spread = asyncio.run(get_historical_data('GOOG', 'GOOGL'))

                upper_bound = average_spread + (0.25 * average_spread)
                lower_bound = average_spread - (0.25 * average_spread)

                if spread > upper_bound:
                    asyncio.run(hedge_position(class_a_info, class_b_info))

                elif spread < lower_bound:
                    asyncio.run(hedge_position(class_b_info, class_a_info))

        time.sleep(0.333)


async def get_spread(class_a, class_b):
    try:
        class_a_api = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(class_a)
        class_b_api = 'https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(class_b)

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

        class_a_avg = 'https://cloud.iexapis.com/stable/stock/{}/stats/day200MovingAvg/?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(class_a)
        class_b_avg = 'https://cloud.iexapis.com/stable/stock/{}/stats/day200MovingAvg/?token=sk_a31d816214bb42f7902c3c63abe6909b'.format(class_b)

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
