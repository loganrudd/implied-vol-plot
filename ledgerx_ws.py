import websocket
import json
import asyncio
from aredis import StrictRedis
# from redistimeseries.client import Client
from ledgerx_api import get_contracts
# redistimeseries docs: https://github.com/RedisTimeSeries/redistimeseries-py
# websocket-client docs: https://github.com/websocket-client/websocket-client

redis_host = 'localhost'
# rts = Client(host=redis_host)
r = StrictRedis(host=redis_host, decode_responses=True)

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
prev_clock = 0


def on_message(ws, raw_message):
    global prev_clock
    message = json.loads(raw_message)
    try:
        update_type = update_types[message['type']]
        ws_contract_id = message['contract_id']
        if message['clock'] == prev_clock:
            return
        prev_clock = message['clock']

        # Publish websocket message to PUBSUB channel
        if update_type == 0:
            channel = f"{ws_contract_id}.{update_type}.{message['status_type']}"
        else:
            channel = f"{ws_contract_id}.{update_type}"
            print(f'publish {channel}: {raw_message}')
            asyncio.run(r.publish(channel, raw_message))
    except KeyError:
        print('Unknown data format:')
        print(message)


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
    active_options = []
    for expiry in option_chain:
        for contract in option_chain[expiry]:
            contract_id = contract['id']
            active_options.append(contract_id)

    url = f"wss://api.ledgerx.com/ws"
    ledgerx_ws = websocket.WebSocketApp(url,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)

    ledgerx_ws.run_forever(ping_interval=25)
