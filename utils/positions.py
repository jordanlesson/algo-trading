from config import alpaca_api
from models.hedged_order import HedgedOrder
from models.order import Order
from streams.trades import hedged_orders


def open_credit_position(expensive_class, cheaper_class, spread, ratio):
    try:
        sell_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='sell', type='limit',
                                             limit_price=expensive_class.ask_price - (0.15 * spread),
                                             time_in_force='gtc')
        buy_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='buy', type='limit',
                                            limit_price=cheaper_class.bid_price + (0.10 * spread),
                                            time_in_force='gtc')

        packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=expensive_class.symbol,
                                    limit_price=float(sell_order.limit_price),
                                    order_type=sell_order.order_type, side=sell_order.side, qty=int(sell_order.qty),
                                    filled_qty=int(sell_order.filled_qty), time_in_force=sell_order.time_in_force,
                                    status=sell_order.status)

        packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=cheaper_class.symbol,
                                   limit_price=float(buy_order.limit_price),
                                   order_type=buy_order.order_type, side=buy_order.side, qty=int(buy_order.qty),
                                   filled_qty=int(buy_order.filled_qty), time_in_force=buy_order.time_in_force,
                                   status=buy_order.status)

        hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side="credit")

        hedged_orders.append(hedged_order)

        print('Credit Spread Order Placed')

        return hedged_order

    except Exception as error:
        print(error)
        return None


def open_debit_position(expensive_class, cheaper_class, spread, ratio):
    try:
        sell_order = alpaca_api.submit_order(cheaper_class.symbol, qty=int(ratio), side='sell', type='limit',
                                             limit_price=cheaper_class.ask_price - (0.10 * spread),
                                             time_in_force='gtc')
        buy_order = alpaca_api.submit_order(expensive_class.symbol, qty=1, side='buy', type='limit',
                                            limit_price=expensive_class.bid_price + (0.15 * spread),
                                            time_in_force='gtc')

        packaged_sell_order = Order(id=sell_order.id, asset_id=sell_order.asset_id, symbol=cheaper_class.symbol,
                                    limit_price=float(sell_order.limit_price),
                                    order_type=sell_order.order_type, side=sell_order.side, qty=int(sell_order.qty),
                                    filled_qty=int(sell_order.filled_qty), time_in_force=sell_order.time_in_force,
                                    status=sell_order.status)

        packaged_buy_order = Order(id=buy_order.id, asset_id=buy_order.asset_id, symbol=expensive_class.symbol,
                                   limit_price=float(buy_order.limit_price),
                                   order_type=buy_order.order_type, side=buy_order.side, qty=int(buy_order.qty),
                                   filled_qty=int(buy_order.filled_qty), time_in_force=buy_order.time_in_force,
                                   status=buy_order.status)

        hedged_order = HedgedOrder(sell_order=packaged_sell_order, buy_order=packaged_buy_order, side="debit")

        hedged_orders.append(hedged_order)

        print('Debit Spread Order Placed')

        return hedged_order

    except Exception as error:
        print(error)
        return None






