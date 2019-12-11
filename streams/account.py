from config import alpaca_api
from models.account import Account
import time

# Global Declaration of Alpaca account data (empty)
account = Account(buying_power=None, portfolio_value=None, reg_t_buying_power=None)


def account_updates():

    global account

    while True:
        try:
            account_info = alpaca_api.get_account()

            account = Account(buying_power=float(account_info.buying_power),
                              portfolio_value=float(account_info.portfolio_value),
                              reg_t_buying_power=float(account_info.regt_buying_power))

        except Exception as error:
            print(error)
        time.sleep(0.5)
