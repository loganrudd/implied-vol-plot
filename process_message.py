import json
from data_provider import load_id_table, write_id_table
from ledgerx_api import get_contract

id_table = load_id_table()
ignore_ids = set()


def process_message(msg):
    global id_table, ignore_ids
    if not id_table:
        id_table = load_id_table()
        print('id_table:', id_table)

    if msg['data'] != 1:
        data = json.loads(msg['data'])
        contract_id = str(data['contract_id'])
        bid, ask = data['bid'] / 100, data['ask'] / 100

        contract_update = {
            'contract_id': contract_id,
            'underlying_asset': None,
            'expiry': None,
            'strike': None,
            'type': None,
            'bid': bid,
            'ask': ask
        }

        if contract_id in ignore_ids:
            return None

        if contract_id in id_table.keys():
            underlying_asset, expiry, strike, option_type = id_table[contract_id]
            contract_update['underlying_asset'] = underlying_asset
            contract_update['expiry'] = expiry
            contract_update['strike'] = strike
            contract_update['type'] = option_type
        else:
            print(f'{contract_id}: not in id_table')
            raw_api_data = get_contract(contract_id)
            if raw_api_data:
                api_data = raw_api_data['data']

                # Drop futures, swaps and ETH contracts
                if api_data['derivative_type'] != 'options_contract' or api_data['underlying_asset'] != 'CBTC':
                    print(f'ignoring:{contract_id}')
                    ignore_ids.add(contract_id)
                    print(ignore_ids)
                    return None

                print('new contract, caching data:')
                print(api_data)
                expiry = api_data['date_expires']
                strike = api_data['strike_price']
                option_type = api_data['type']
                underlying_asset = api_data['underlying_asset']
                id_table[contract_id] = (expiry, strike, option_type)
                contract_update['underlying_asset'] = underlying_asset
                contract_update['expiry'] = expiry
                contract_update['strike'] = strike
                contract_update['type'] = option_type
                write_id_table(id_table)

        return contract_update
