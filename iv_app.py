from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, AjaxDataSource, CustomJS
from bokeh.plotting import figure
import redis

from multiprocessing import Process
from time import sleep

from data_provider import get_btc_price, get_expirys, get_expiry_data

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

# Figures
iv_plot = figure(plot_width=800, plot_height=300)

# Controls
expirys = get_expirys()
expiry_keys, expiry_labels = zip(*expirys)
# expiry_select = Select(value=expiry_labels[0], options=expirys)
# option_type_radiobutton = RadioButtonGroup(labels=['Calls', 'Puts'], active=1)
# top_controls = row(expiry_select, option_type_radiobutton)

# TODO: loop over expirations and make a grid of plots
layout = column(iv_plot)

adapter = CustomJS(code="""
    var price = cb_data.response['data']['amount']
    var data = {x: [price], y: [0]}
    console.log(price)
    return data 
""")

# Datasources
#theo_source = ColumnDataSource()
#iv_pts_source = ColumnDataSource()
#bid_iv_source = ColumnDataSource()
#ask_iv_source = ColumnDataSource()
btc_price_source = AjaxDataSource(data_url='https://api.coinbase.com/v2/prices/BTC-USD/spot',
                                  method='GET',
                                  polling_interval=3000, adapter=adapter)


def init_plots():
    # Labels
    iv_plot.yaxis.axis_label = 'IV%'
    iv_plot.xaxis.axis_label = 'Strike'

    # iv_plot.x(source=iv_pts_source, color='yellow', legend_label='Mid IV')
    # iv_plot.triangle(source=ask_iv_source, angle=3.14, color='red', fill_color='red', legend_label='Ask IV')
    # iv_plot.triangle(source=bid_iv_source, fill_color='blue', legend_label='Bid IV')

    # Line for BTC price
    iv_plot.ray(source=btc_price_source, color='cyan', legend_label='BTC Price',
                length=0, angle=90, angle_units='deg')

# option_type_radiobutton.on_change('active', update_data)


def update_data(data):
    # TODO: take the data and feed it into charts
    #  maybe we want to have all the expirations displayed at once
    # print(data)
    return


def btc_price_poller():
    def update_datasource():
        global btc_price_source

        price = float(get_btc_price())
        print(price)
        btc_price_source.data = dict(x=[price], y=[0])
        sleep(3)

    while True:
        doc.add_next_tick_callback(update_datasource)


def sub_listener():
    for msg in p.listen():
        doc.add_next_tick_callback(update_data(msg))


# Initialize Bokeh plot
init_plots()
doc.theme = 'night_sky'
doc.add_root(layout)
doc.title = "IV Chart"

# Polling datasource for BTC price


sub_process = Process(target=sub_listener)
sub_process.start()
# sub_process.join()
