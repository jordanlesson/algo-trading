from alpaca_trade_api import StreamConn
from models.order import Order
from models.position import Position
from streams.stocks import stock_a, stock_b
import time
from config import alpaca_key_id, alpaca_secret_key, alpaca_base_url


# Declaration of stream
conn = StreamConn(
    key_id=alpaca_key_id,
    secret_key=alpaca_secret_key,
    base_url=alpaca_base_url,
)

# Global Declaration of our positions, orders, and hedged orders (empty)
positions = []
orders = []
hedged_orders = []

hedging = False


def trade_updates():
    conn.run(['trade_updates'])


# Function that is called whenever an order update occurs (new orders, fills, partial fills, cancels, etc...)
@conn.on(r'^trade_updates$')
async def on_trade_updates(conn, channel, data):
    # global orders
    # global positions

    order_data = data
    order = order_data.order
    packaged_order = Order(id=order["id"], asset_id=order["asset_id"], symbol=order["symbol"],
                           limit_price=order["limit_price"],
                           order_type=order["order_type"], qty=order["qty"],
                           filled_qty=order["filled_qty"], side=order["side"], time_in_force=order["time_in_force"],
                           status=order["status"])

    if order_data.event == "new":
        orders.append(packaged_order)
    elif order_data.event == "fill":
        if orders.count(packaged_order) > 0:
            orders.remove(packaged_order)

        position_exists = False

        if len(positions) != 0:
            for position in positions:
                if position.order_id == packaged_order.id:
                    position_exists = True
                    position_index = positions.index(position)
                    position_side = None
                    if packaged_order.side == "buy":
                        position_side = "long"
                    else:
                        position_side = "short"
                    positions[position_index] = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                                         order_id=packaged_order.id, qty=packaged_order.qty,
                                                         side=position_side)

            if not position_exists:
                position_side = None
                if packaged_order.side == "buy":
                    position_side = "long"
                else:
                    position_side = "short"
                packaged_position = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                             order_id=packaged_order.id, qty=packaged_order.qty, side=position_side)
                positions.append(packaged_position)
        else:
            position_side = None
            if packaged_order.side == "buy":
                position_side = "long"
            else:
                position_side = "short"
            packaged_position = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                         order_id=packaged_order.id, qty=packaged_order.qty, side=position_side)
            positions.append(packaged_position)

    elif order_data.event == "partial_fill":
        if orders.count(packaged_order) > 0:
            order_index = orders.index(packaged_order)
            orders[order_index] = packaged_order

        if len(positions) != 0:
            for position in positions:
                if position.order_id == packaged_order.id:
                    position_exists = True
                    position_index = positions.index(position)
                    position_side = None
                    if packaged_order.side == "buy":
                        position_side = "long"
                    else:
                        position_side = "short"
                    positions[position_index] = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                                         order_id=packaged_order.id, qty=packaged_order.filled_qty,
                                                         side=position_side)

            if not position_exists:
                position_side = None
                if packaged_order.side == "buy":
                    position_side = "long"
                else:
                    position_side = "short"
                packaged_position = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                             order_id=packaged_order.id, qty=packaged_order.filled_qty,
                                             side=position_side)
                positions.append(packaged_position)
        else:
            position_side = None
            if packaged_order.side == "buy":
                position_side = "long"
            else:
                position_side = "short"
            packaged_position = Position(asset_id=packaged_order.asset_id, symbol=packaged_order.symbol,
                                         order_id=packaged_order.id, qty=packaged_order.qty, side=position_side)
            positions.append(packaged_position)

    elif order_data.event == "canceled" or order_data.event == "expired":
        if orders.count(packaged_order) > 0:
            orders.remove(packaged_order)
