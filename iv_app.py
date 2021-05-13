from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, RadioButtonGroup
from bokeh.plotting import figure
from multiprocessing import Process

from data_provider import get_expirys, get_expiry_data
import redis

r = redis.Redis(host='localhost')
p = r.pubsub()
p.psubscribe('*.1')

'''
IV Chart Bokeh App

Docs: https://docs.bokeh.org/en/latest/docs/user_guide/server.html
Good Example: https://github.com/bokeh/bokeh/blob/branch-2.4/examples/app/stocks/main.py

`bokeh serve --show iv_app.py` from the project root

Looking to plot bid/ask and theoretical price (and orders eventually)
'''
# Main Bokeh Doc
doc = curdoc()

# Figures
price_plot = figure(plot_width=800, plot_height=300)
iv_plot = figure(plot_width=800, plot_height=300, x_range=price_plot.x_range)

# Controls
expirys = get_expirys()
expiry_keys, expiry_labels = zip(*expirys)
expiry_select = Select(value=expiry_labels[0], options=expirys)
option_type_radiobutton = RadioButtonGroup(labels=['Calls', 'Puts'], active=1)
top_controls = row(expiry_select, option_type_radiobutton)
layout = column(top_controls, price_plot, iv_plot)

# Datasources
bid_source = ColumnDataSource()
ask_source = ColumnDataSource()
theo_source = ColumnDataSource()
iv_pts_source = ColumnDataSource()
bid_iv_source = ColumnDataSource()
ask_iv_source = ColumnDataSource()
btc_price_source = ColumnDataSource()


def init_plots():
    expiry_select.value = expiry_keys[0]

    # Labels
    price_plot.yaxis.axis_label = 'Price'
    iv_plot.yaxis.axis_label = 'IV%'
    iv_plot.xaxis.axis_label = 'Strike'

    price_plot.triangle(source=ask_source, angle=3.14, color='red', fill_color='red', legend_label='Ask')
    price_plot.triangle(source=bid_source, fill_color='blue', legend_label='Bid')
    price_plot.x(source=theo_source, size=10, color='orange', legend_label='Theo price')

    iv_plot.x(source=iv_pts_source, color='yellow', legend_label='Mid IV')
    iv_plot.triangle(source=ask_iv_source, angle=3.14, color='red', fill_color='red', legend_label='Ask IV')
    iv_plot.triangle(source=bid_iv_source, fill_color='blue', legend_label='Bid IV')

    # Line for mid price of nearest BTC future
    price_plot.ray(source=btc_price_source, color='cyan', legend_label='BTC Price',
                   length=0, angle=90, angle_units='deg')
    iv_plot.ray(source=btc_price_source, color='cyan', legend_label='BTC Price',
                length=0, angle=90, angle_units='deg')


# expiry_select.on_change('value', update_data)
# option_type_radiobutton.on_change('active', update_data)

def update_data(data):
    # TODO: take the data and feed it into charts
    #  maybe we want to have all the expirations displayed at once
    print(data)


def sub_listener():
    for msg in p.listen():
        curdoc().add_next_tick_callback(update_data(msg))


# Initialize Bokeh plot
init_plots()
doc.theme = 'night_sky'
curdoc().add_root(layout)
curdoc().title = "IV Chart"

# Start separate process to listen to PUBSUB channel
sub_process = Process(target=sub_listener)
sub_process.start()
# sub_process.join()
