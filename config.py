import alpaca_trade_api as alpaca

# Declaration of Alpaca API
alpaca_key_id = 'PKHA7WCY5AA9TJZ9VOA3'
alpaca_secret_key = 'eruIP2dxF4AEpD6/ZfZOnK40qbLN5yEfbgX164tB'
alpaca_base_url = 'https://paper-api.alpaca.markets'

alpaca_api = alpaca.REST(
    key_id=alpaca_key_id,
    secret_key=alpaca_secret_key,
    base_url=alpaca_base_url,
)
