from functools import lru_cache
from ledgerx_api import get_contracts, get_book_state
import requests
import json
import arrow

from market import get_vol, get_price

contracts = get_contracts()
option_chain = contracts['option_chain']
futures = contracts['futures_contracts']


def load_id_table():
    # loads id_table to look up (strike, type) tuple from contract_id key
    with open('id_table.json', 'r') as f:
        raw_json = f.read()
        id_table = json.loads(raw_json)
    return id_table

id_table = load_id_table()


def write_id_table(id_table=None):
    if not id_table:
        id_table = {}
        options = get_contracts(active=True)['option_chain']
        for expiry in options.keys():
            for option in options[expiry]:
                id_table[option['id']] = (option['strike_price'], option['type'])

    with open('id_table.json', 'w') as f:
        f.write(json.dumps(id_table))
        print(id_table)
        print('...written to id_table.json')


def get_btc_price():
    # Get BTC price from Coinbase API
    resp = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot')
    price = resp.json()['data']['amount']
    return price


def get_expirys():
    expirys = []
    now = arrow.utcnow()
    # loops over expiration datetime strings and filters for expirations in the future
    for expiry in list(option_chain.keys()):
        expiry_date = arrow.get(expiry)
        if now < expiry_date:
            fmt = 'MM-DD-YY'
            label = expiry_date.format(fmt)
            expirys.append((expiry, label))

    # Reverse our relevant dates to make the nearest expiry [0]
    expirys.reverse()
    return expirys


@lru_cache()
def get_expiry_data(expiry_key, option_type):
    now = arrow.utcnow()
    expiry_series = option_chain[expiry_key]
    asks = []
    bids = []
    mids = []
    book_top = []
    max_size = 0
    high_strike = 0
    low_strike = 10e9
    btc_price = get_btc_price()

    # Every contract is different strike
    for contract in expiry_series:

        if option_type == 0 and contract['type'] == 'put':
            continue
        if option_type == 1 and contract['type'] == 'call':
            continue

        strike = contract['strike_price']/100
        if strike > high_strike:
            high_strike = strike
        if strike < low_strike:
            low_strike = strike

        book_state = get_book_state(contract['id'], cache=True)['data']['book_states']
        print('asdf:', book_state)

        high_bid = 0
        low_ask = 10e9

        for state in book_state:
            price = state['price']/100
            size = state['size']
            if size > max_size:
                max_size = size

            # find top of orderbook
            if state['is_ask'] and price < low_ask:
                low_ask = price
            elif not state['is_ask'] and price > high_bid:
                high_bid = price

        book_top.append((strike, high_bid, low_ask))
        mid = (high_bid + low_ask) / 2
        mids.append((strike, mid))

        # Loop over again, not sure how to avoid this because
        # we need to find mid before filtering orders to remove outliers
        for state in book_state:
            price = state['price']/100
            if abs(price - mid) < (low_ask - high_bid) * 2:
                if state['is_ask']:
                    asks.append((price, strike, size))
                else:
                    bids.append((price, strike, size))

    # Mid line
    # Sort by strike price (x_axis)
    # https://stackoverflow.com/a/9764364
    mids = sorted(mids)
    strikes, mid_price = zip(*mids)

    # Get top of order book bid/ask to calc IV
    # Calculate IV skew plot from spline mid prices
    # TODO: figure out how to use seconds and division to get partial days
    dte = (arrow.get(expiry_key) - now).days
    if option_type == 1:
        flag = 'p'
    else:
        flag = 'c'

    # Here create series of IV for top bid and ask prices
    bid_iv = []
    ask_iv = []
    for strike, bid, ask in book_top:
        attrs = {
            'price': bid,
            'dte': dte,
            'ul_price': btc_price,
            'strike': strike,
            'flag': flag
        }
        bid_vol = get_vol(attrs)
        if bid_vol == 0:
            continue
        bid_iv.append((strike, bid_vol))
        attrs['price'] = ask
        ask_iv.append((strike, get_vol(attrs)))

    # Finally return a dict of all the different series for the data sources
    return {
        'btc_price': btc_price,
        'bids': bids,
        'asks': asks,
        'mids': mids,
        'ask_iv': ask_iv,
        'bid_iv': bid_iv
    }
