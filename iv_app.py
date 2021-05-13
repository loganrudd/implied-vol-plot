from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import AjaxDataSource, CustomJS
from bokeh.plotting import figure
import redis

from multiprocessing import Process
from math import ceil
from collections import defaultdict

from data_provider import get_expirys

r = redis.Redis(host='localhost')
p = r.pubsub()
p.psubscribe('*.1')

'''
IV Chart Bokeh App

Bokeh App Docs: https://docs.bokeh.org/en/latest/docs/user_guide/server.html

`bokeh serve --show iv_app.py` from the project root

Live plot bid/mid/ask IV and BTC price
'''
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
plots = {}

# TODO: Fix issue with browser console error: could not set initial ranges, have y-axis 0 at bottom and locked, etc
for expiry in expiry_labels:
    plot = figure(plot_width=600, plot_height=300)
    plot.yaxis.axis_label = 'IV%'
    plot.xaxis.axis_label = 'Strike'
    plot.ray(source=btc_price_source, color='cyan', legend_label='BTC Price',
             length=0, angle=90, angle_units='deg')
    plots[expiry] = plot

num_rows = ceil(len(expiry_labels) / 3)

rows = defaultdict(list)
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


def update_data(data):
    # TODO: take the data and feed it into charts -- from ledgerx_ws.py publisher
    #  maybe we want to have all the expirations displayed at once
    # print(data)
    return


def sub_listener():
    for msg in p.listen():
        doc.add_next_tick_callback(update_data(msg))


# Initialize Bokeh plot
doc.theme = 'night_sky'
doc.add_root(layout)
doc.title = "IV Chart"

sub_process = Process(target=sub_listener)
sub_process.start()
# sub_process.join()
