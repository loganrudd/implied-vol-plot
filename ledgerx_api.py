import requests
import pandas as pd
from collections import defaultdict
import pickle
from time import sleep

# https://docs.ledgerx.com/reference

headers = {
    "Accept": "application/json",
}

def get_contracts(active=True):
    # defaultdict(list) so we can just append() contracts to the dict date keys
    # Key: Date string, item: option contract dict
    option_chain = defaultdict(list)
    day_ahead_swaps = []
    futures_contracts = []

    def recurse_contracts(url="https://api.ledgerx.com/trading/contracts"):
        resp = requests.get(url, headers=headers, params=dict(active=active)).json()
        data = resp['data']

        # meta has information on how large the whole dataset is and next page URL
        meta = resp['meta']

        for contract in data:
            # Seems like there's three types of derivative_type: day_ahead_swap, future_contract, options_contract
            derivative_type = contract['derivative_type']
            if derivative_type == 'options_contract':
                option_chain[contract['date_expires']].append(contract)
            elif derivative_type == 'day_ahead_swap':
                day_ahead_swaps.append(contract)
            elif derivative_type == 'future_contract':
                futures_contracts.append(contract)

        # Check if there's another page
        next_url = meta['next']
        if next_url:
            sleep(0.1)
            recurse_contracts(next_url)

    # Starts here
    contracts = {
        'option_chain': option_chain,
        'day_ahead_swaps': day_ahead_swaps,
        'futures_contracts': futures_contracts
    }

    try:
        # Delete contracts.pkl to re-download
        contracts = pickle.load(open('contracts.pkl', 'rb'))
        print('Loading contracts from pickle cache...')

    except FileNotFoundError:
        print('Downloading contracts from LedgerX... Please Wait...')
        recurse_contracts()
        pickle.dump(contracts, open('contracts.pkl', 'wb'))

    return contracts


def get_book_state(id, cache=False):

    def get_state():
        url = f"https://trade.ledgerx.com/api/book-states/{id}"
        resp = requests.get(url, headers=headers).json()
        return resp

    # Takes contract id and returns orderbook state
    if cache:
        try:
            return pickle.load(open(f'./book_states/{id}.pkl', 'rb'))
        except FileNotFoundError:
            book_state = get_state()
            pickle.dump(book_state, open(f'./book_states/{id}.pkl', 'wb'))
            return book_state

    return get_state()


def get_trade_history():
    trade_history = []

    def recurse_trades(url="https://api.ledgerx.com/trading/trades"):
        resp = requests.get(url, headers=headers).json()
        data = resp['data']

        # meta has information on how large the whole dataset is and next page URL
        meta = resp['meta']

        for trade in data:
            trade_history.append(trade)

        # Check if there's another page
        next_url = meta['next']
        if next_url:
            sleep(0.1)
            recurse_trades(next_url)

    try:
        # Delete trade_history.pkl to re-download
        trade_history = pickle.load(open('trade_history.pkl', 'rb'))
        print('Loading trades from pickle cache...')

    except FileNotFoundError:
        print('Downloading trade history from LedgerX... Please Wait...')
        recurse_trades()
        pickle.dump(trade_history, open('trade_history.pkl', 'wb'))

    return trade_history


if __name__ == "__main__":
    # Goal with this is to build an orderbook on our side that gets updated with their websocket endpoint
    # the get_contracts() function returns a pretty big chunk of data (over 7000 entries with tens of properties per)
    contracts = get_contracts()
    option_chain = contracts['option_chain']
    
    # Looks like they have all their expired contracts listed too, back to 10/27/2017 at the end
    print(option_chain.keys())

    # This is the April 30th expiration
    expiry_str = '2021-04-30 20:00:00+0000'
    apr_expiry = option_chain[expiry_str]
    print(f'{len(apr_expiry)} contracts for {expiry_str} expiration')

    # Loop over every contract in 4/30/21 expiry and get orderbook state
    for contract in apr_expiry:
        print(contract['label'])
        book = get_book_state(contract['id'])
        sleep(0.5)
        for entry in book['data']['book_states']:
            # TODO: save data to DB, MongoDB, Redis whatever to be updated by websocket
            print(entry)
