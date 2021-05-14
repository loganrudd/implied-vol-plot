import json
from data_provider import id_table, write_id_table
from ledgerx_api import get_contract


def process_message(msg):
    if msg['data'] != 1:
        data = json.loads(msg['data'])
        contract_id = data['contract_id']
        bid, ask = data['bid'] / 100, data['ask'] / 100
        print(contract_id, bid, ask)

        try:
            contract_info = id_table[contract_id]
            print(contract_info)
        except KeyError:
            contract_data = get_contract(contract_id)
            if contract_data:
                contract_data = contract_data['data']
                print('new contract, caching data:')
                print(contract_data)
                id_table[contract_id] = (contract_data['strike_price'], contract_data['type'])
            else:
                return
