import alpaca_trade_api as alpaca
from models.account import Account
from main import account
import time

# Declaration of Alpaca API
# noinspection SpellCheckingInspection
alpaca_api = alpaca.REST(
    key_id='PKMHQUWERAMULK15DY13',
    secret_key='FpaNeZgF1mDg0J3nVuqWklSRfcRsh60ZioTOjccc',
    base_url='https://paper-api.alpaca.markets',
)


def account_updates():
    # global account
    while True:
        try:
            account_info = alpaca_api.get_account()
            account = Account(buying_power=float(account_info.buying_power),
                              portfolio_value=float(account_info.portfolio_value),
                              reg_t_buying_power=float(account_info.regt_buying_power))
        except Exception as error:
            print(error)
        time.sleep(0.5)
