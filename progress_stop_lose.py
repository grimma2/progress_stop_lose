from tinkoff.invest import Client, OrderDirection, OrderType, Quotation
from uuid import uuid4
from pandas_datareader import DataReader

from datetime import datetime
from os import environ


TOKEN = environ.get('TOKEN')
STOCK = {'quantity': 2, 'figi': 'BBG004RVFFC0', 'account_id': '2090472255'}
STOP_LOSE_PER_SENT = 0.02
ORDER_DO_PRICE = 0.00
ORDER_ID = None
ORDER_ACTIVE = True


def get_share_price(ticker) -> float:
    str_price = DataReader(
        ticker, data_source='yahoo', start=str(datetime.now()).split(' ')[0]
    )['Close'].to_string().split('  ')[-1]
    return float(str_price)


def order(client_: Client, order_type, share_):
    global ORDER_DO_PRICE, ORDER_ID
    ORDER_ID = ''.join(list(str(uuid4().int))[:36])
    ORDER_DO_PRICE = share_*(1-STOP_LOSE_PER_SENT)
    units, nano = str(ORDER_DO_PRICE).split('.')
    client_.orders.post_order(
        **STOCK, **{
            'order_id': ORDER_ID,
            'direction': OrderDirection.ORDER_DIRECTION_SELL,
            'order_type': order_type,
            'price': Quotation(units=int(units), nano=int(nano))
        }
    )


with Client(TOKEN) as client:
    while ORDER_ACTIVE:
        share = get_share_price('BABA')
        if client.orders.get_orders(account_id='2090472255').orders:
            last_order = client.orders.get_orders(account_id='2090472255').orders[-1]
            if last_order.execution_report_status == 4 or 5:
                if share*(1-STOP_LOSE_PER_SENT) > (ORDER_DO_PRICE+share*(STOP_LOSE_PER_SENT*0.2)):
                    client.orders.cancel_order(account_id='2090472255', order_id=ORDER_ID)
                    order(client_=client, order_type=OrderType.ORDER_TYPE_LIMIT, share_=share)
            elif last_order.execution_report_status == 1:
                ORDER_ACTIVE = False
        else:
            order(client_=client, order_type=OrderType.ORDER_TYPE_LIMIT, share_=share)
