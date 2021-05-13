from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import AjaxDataSource, CustomJS
from bokeh.plotting import figure
from aredis import StrictRedis

import asyncio
import json
from math import ceil
from collections import defaultdict
from functools import partial

from data_provider import get_expirys
from ledgerx_api import get_contract

'''
IV Chart Bokeh App

Bokeh App Docs: https://docs.bokeh.org/en/latest/docs/user_guide/server.html

`bokeh serve --show iv_app.py` from the project root

Live plot bid/mid/ask IV and BTC price
'''

# Redis setup
r = StrictRedis(host='localhost')
p = r.pubsub()

# Main Bokeh Doc
doc = curdoc()

# Bitcoin price datasource
adapter = CustomJS(code="""
    var price = cb_data.response['data']['amount']
    var data = {x: [price], y: [0]}
    console.log(price)
    return data 
""")
btc_price_source = AjaxDataSource(data_url='https://api.coinbase.com/v2/prices/BTC-USD/spot',
                                  method='GET',
                                  polling_interval=3000, adapter=adapter)


# Controls
expirys = get_expirys()
expiry_keys, expiry_labels = zip(*expirys)
# option_type_radiobutton = RadioButtonGroup(labels=['Calls', 'Puts'], active=1)
# top_controls = row(option_type_radiobutton)

# Loop over expirations and make grid of plots
# one plot per expiration (6 of them, two rows of 3)
plots = {}

# TODO: Fix issue with browser console error: could not set initial ranges, have y-axis 0 at bottom and locked, etc
for expiry in expiry_labels:
    plot = figure(plot_width=600, plot_height=300)
    plot.yaxis.axis_label = 'IV%'
    plot.xaxis.axis_label = 'Strike'
    plot.ray(source=btc_price_source, color='cyan', length=0, angle=90, angle_units='deg')
    plots[expiry] = plot


rows = defaultdict(list)
num_rows = ceil(len(expiry_labels) / 3)
for n_row in range(0, num_rows):
    for n_column in range(0, 3):
        try:
            expiry = expiry_labels[(n_row * 3) + n_column]
            rows[n_row].append(plots[expiry])
        except IndexError:
            print('end of expirys')
            continue

layout_rows = []
for row_k in rows.keys():
    layout_rows.append(row(children=rows[row_k]))

layout = column(children=layout_rows)


def update_data(msg):
    # TODO: take the data and feed it into charts -- from ledgerx_ws.py publisher

    if msg['data'] != 1:
        data = json.loads(msg['data'])
        contract_id = data['contract_id']
        bid, ask = data['bid']/100, data['ask']/100
        print(contract_id, bid, ask)

        # TODO: get get_contract(contract_id) to speed up, using lrucache right now,
        #  could be combined with pickling responses (even into redis) so cache will persist
        contract_info = get_contract(contract_id)
        print(contract_info)


async def sub_listener():
    await p.psubscribe('*.1')

    while True:
        msg = await p.get_message()
        doc.add_next_tick_callback(partial(update_data, msg))


# Initialize Bokeh plot
doc.theme = 'night_sky'
doc.add_root(layout)
doc.title = "IV Chart"

asyncio.ensure_future(sub_listener())
