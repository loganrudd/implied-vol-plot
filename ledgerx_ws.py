import websocket
import json
import redis
from ledgerx_api import get_contracts
# redistimeseries docs: https://github.com/RedisTimeSeries/redistimeseries-py
# websocket-client docs: https://github.com/websocket-client/websocket-client

redis_host = 'localhost'
r = redis.Redis(host=redis_host, decode_responses=True)

# Lua script to do a conditional publish/store to TS (only clock > prev_clock)
lua_cond_pub = """
local prev_clock = redis.call('GETSET', KEYS[1], ARGV[1])
local clock = tonumber(ARGV[1])
prev_clock = tonumber(prev_clock)
if(clock > prev_clock) then
    redis.call('PUBLISH', ARGV[2], ARGV[5])
    redis.call('TS.MADD', KEYS[2], ARGV[3], KEYS[3], ARGV[4])
    return 1
else
    return 0
end
"""
cond_pub = r.register_script(lua_cond_pub)


def on_message(ws, raw_message):
    message = json.loads(raw_message)
    try:
        ws_contract_id = message['contract_id']
        clock = message['clock']
        bid = message['bid']
        ask = message['ask']

        # Publish websocket message to PUBSUB channel
        channel = f"{ws_contract_id}.1"
        lua_keys = [f'{ws_contract_id}:clock', f'{ws_contract_id}:bid', f'{ws_contract_id}:ask']
        lua_args = [clock, channel, bid, ask, raw_message]
        cond_pub(keys=lua_keys, args=lua_args)
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
    url = f"wss://api.ledgerx.com/ws"
    r.flushdb()
    ledgerx_ws = websocket.WebSocketApp(url,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)

    ledgerx_ws.run_forever(ping_interval=25)
