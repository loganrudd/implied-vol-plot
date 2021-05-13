import os
import redis
import websocket
import json
# from redistimeseries.client import Client
from ledgerx_api import get_contracts
# redistimeseries docs: https://github.com/RedisTimeSeries/redistimeseries-py
# websocket-client docs: https://github.com/websocket-client/websocket-client

redis_host = 'localhost'
# rts = Client(host=redis_host)
r = redis.Redis(host=redis_host, decode_responses=True)

# Dict to encode update type to int
update_types = {
    "action_report": 0,
    "book_top": 1,
    "auth_success": 2,
    "heartbeat": 3,
    "collateral_balance_update": 4,
    "open_positions_update": 5,
    "exposure_reports": 6,
    "contract_added": 7,
    "contract_removed": 8,
    "trade_busted": 9,
    "unauth_success": 10
}

contract_types = {}

def on_message(ws, raw_message):
    message = json.loads(raw_message)
    try:
        update_type = update_types[message['type']]
        ws_contract_id = message['contract_id']

        # Publish websocket message to PUBSUB channel
        if update_type == 0:
            channel = f"{ws_contract_id}.{update_type}.{message['status_type']}"
        else:
            channel = f"{ws_contract_id}.{update_type}"
        print(f'publish {channel}: {raw_message}')
        r.publish(channel, raw_message)

        if update_type == 1:
            # book_top
            data_tuples = [(f'{contract_id}:{side}', '*', message[side]) for side in ['bid', 'ask']]
            # rts.madd(data_tuples)

        elif update_type in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
            # auth_success, heartbeat, account stats, etc...
            # just skip over them for now
            return

    except KeyError:
        print('***** No "type" or unknown type in message:')
        #print(message)


def on_error(ws, error):
    print("***ERROR:")
    print(error)


def on_close(ws):
    print('### closed ###')


def on_open(ws):
    print('connection open')


if __name__ == "__main__":
    # websocket.enableTrace(True)
    # Initialize database state:
    # get currently active contracts
    contracts = get_contracts()
    option_chain = contracts['option_chain']

    # Loop over options
    r.delete('active_options')
    active_options = []
    for expiry in option_chain:
        for contract in option_chain[expiry]:
            contract_id = contract['id']
            active_options.append(contract_id)

    # Add active options to 'active_options' Redis set
    r.sadd('active_options', *active_options)

    # Get set difference between has_ts and active_options to get expired series to remove
    dead_options = r.sdiff('has_ts', 'active_options')
    print('dead_options:', dead_options)

    # move the timeseries to another database to be stored to disk eventually, remove from has_ts set
    # TODO: write scheduler to move data from db 3 to disk w/metadata
    for dead_contract_id in dead_options:
        print(f'moving dead contract TS:{dead_contract_id}...')
        for side in ['bid', 'ask']:
            r.move(f'{dead_contract_id}:{side}', 3)
            r.srem('has_ts', dead_contract_id)

    # flipped set difference now to find new contracts that need timeseries created
    needs_ts = r.sdiff('active_options', 'has_ts')
    print('needs_ts', needs_ts)
    for needy_contract_id in needs_ts:
        for side in ['bid', 'ask']:
            # rts.create(f'{needy_contract_id}:{side}', labels={'contract_id': needy_contract_id})
            r.sadd('has_ts', needy_contract_id)
            print(f'adding {needy_contract_id}...')

    url = f"wss://api.ledgerx.com/ws"
    ledgerx_ws = websocket.WebSocketApp(url,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)

    ledgerx_ws.run_forever(ping_interval=25)
