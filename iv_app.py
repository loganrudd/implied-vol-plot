from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import AjaxDataSource, ColumnDataSource, CustomJS, RadioButtonGroup
from bokeh.plotting import figure
from aredis import StrictRedis

import asyncio
from math import ceil
from collections import defaultdict
from functools import partial

from process_message import process_message
from data_provider import get_expirys, load_id_table

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
print(expirys)
expiry_keys, expiry_labels = zip(*expirys)
option_type_radiobutton = RadioButtonGroup(labels=['Calls', 'Puts'], active=1)
top_controls = row(option_type_radiobutton)

# load id_table so we can generate our DataColumnSources from it
# data_sources[<'put' | 'call'>][expiration][<'bid' | 'ask'>] retrieves a ColumnDataSource of scheme:
# {'x': <strike prices>, 'y': <IV%>}
data_sources = defaultdict(partial(defaultdict, dict))
id_table = load_id_table()
for option_type in ['call', 'put']:
    for expiry in expiry_keys:
        for contract_id in id_table.keys():
            contract_expiry = id_table[contract_id][0]
            contract_strike = id_table[contract_id][1]
            contract_option_type = id_table[contract_id][2]
            if contract_option_type == option_type and contract_expiry == expiry:
                data_sources[option_type][expiry]['bid'] = ColumnDataSource()
                data_sources[option_type][expiry]['ask'] = ColumnDataSource()

# Loop over expirations and make grid of plots
# one plot per expiration (6 of them, two rows of 3)
plots = {}
# TODO: Fix issue with browser console error: could not set initial ranges, have y-axis 0 at bottom and locked, etc
for expiry_key, expiry_label in expirys:
    plot = figure(title=f'{expiry_label} Expiration', plot_width=600, plot_height=300)
    plot.yaxis.axis_label = 'IV%'
    plot.xaxis.axis_label = 'Strike'
    plot.ray(source=btc_price_source, color='cyan', length=0, angle=90, angle_units='deg')
    plots[expiry_key] = plot


rows = defaultdict(list)
num_rows = ceil(len(expiry_keys) / 3)
for n_row in range(0, num_rows):
    for n_column in range(0, 3):
        try:
            expiry = expiry_keys[(n_row * 3) + n_column]
            rows[n_row].append(plots[expiry])
        except IndexError:
            print('end of expirys')
            continue

layout_rows = [top_controls]
for row_k in rows.keys():
    layout_rows.append(row(children=rows[row_k]))

layout = column(children=layout_rows)


def update_data(msg):
    data = process_message(msg)
    if data:
        print('data:', data)


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
