from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, RadioButtonGroup, Slider
from bokeh.plotting import figure

from data_provider import get_expirys, get_expiry_data
'''
IV Chart Bokeh App

Docs: https://docs.bokeh.org/en/latest/docs/user_guide/server.html
Good Example: https://github.com/bokeh/bokeh/blob/branch-2.4/examples/app/stocks/main.py

`bokeh serve --show iv_app.py` from the project root

Looking to plot bid/ask and theoretical price (and orders eventually)
'''

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
    # setting expiry_select value triggers update_data
    # initializing plot data sources(also had to do it because of maybe a bug in bokeh)
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


# Callbacks and event setup
def update_data(attrname, old, new):
    selected_expiry = expiry_select.value
    option_type = option_type_radiobutton.active

    # upper price chart
    bid_price, bid_strike, bid_size = zip(*data['bids'])
    ask_price, ask_strike, ask_size = zip(*data['asks'])
    theo_strike, theo_price = zip(*data['theo'])
    bid_source.data = dict(x=bid_strike, y=bid_price)
    ask_source.data = dict(x=ask_strike, y=ask_price)
    theo_source.data = dict(x=theo_strike, y=theo_price)

    # BTC price marker
    btc_price_source.data = dict(x=[data['btc_price']], y=[0])

    # lower IV chart
    iv_strike, iv_pts = zip(*data['ivs'])
    bid_iv_strike, bid_iv_pts = zip(*data['bid_iv'])
    ask_iv_strike, ask_iv_pts = zip(*data['ask_iv'])
    bid_iv_source.data = dict(x=bid_iv_strike, y=bid_iv_pts)
    ask_iv_source.data = dict(x=ask_iv_strike, y=ask_iv_pts)
    iv_pts_source.data = dict(x=iv_strike, y=iv_pts)


expiry_select.on_change('value', update_data)
option_type_radiobutton.on_change('active', update_data)

init_plots()

curdoc().theme = 'night_sky'
curdoc().add_root(layout)
curdoc().title = "IV Chart"
