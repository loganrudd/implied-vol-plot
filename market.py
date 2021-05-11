from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_lets_be_rational.exceptions import BelowIntrinsicException, AboveMaximumException
import numpy as np

# need to have something that can setup a simulation for a market
# so the account can ask for the underlying price, price for options, etc
# http://www.vollib.org/documentation/python/1.0.2/apidoc/py_vollib.black_scholes.html

# TODO: make this a class that gets initialized with market_data attrs
market_data = {
    'interest_rate': 0.01,
    'iv': 0.6424
}


def get_vol(attrs):
    option_price = attrs['price']
    ul_price = attrs['ul_price']
    dte = attrs['dte']
    strike = attrs['strike']
    flag = attrs['flag']
    interest = market_data['interest_rate']
    try:
        iv = implied_volatility(option_price, ul_price, strike, dte/365, interest, flag)
    except BelowIntrinsicException:
        # print('Below Intrinsic: return NaN')
        iv = np.nan
    except AboveMaximumException:
        print('Vol above max value')
        iv = np.nan
    return iv


def get_price(attrs):
    ul_price = attrs['ul_price']
    dte = attrs['dte']
    strike = attrs['strike']
    flag = attrs['flag']
    iv = attrs['iv']
    interest = market_data['interest_rate']
    price = black_scholes(flag, ul_price, strike, dte/365, interest, iv)
    return price


def vol_example():
    ul_price = 60200
    strike = 60000
    dte = 4.5
    interest = market_data['interest_rate']
    option_price_mid = 2200

    iv = implied_volatility(option_price_mid, ul_price, strike, dte/365, interest, 'p')
    print(f'Put iv:{iv}')


def pricing_example():
    ul_price = 60200
    strike = 58000
    dte = 4.5
    iv = market_data['iv']
    interest = market_data['interest_rate']
    # black_scholes(flag, S(ul_price), K(strike), t(time to expiry in years), r(int rate), sigma(imp vol))

    # This returns the theoretical price of a call/put using Black-Scholes:
    # call:1869.457951280331 put:2862.952205291236
    call_price = black_scholes('c', ul_price, strike, dte/365, interest, iv)
    put_price = black_scholes('p', ul_price, strike, dte/365, interest, iv)
    print(f"call:{call_price}, put:{put_price}")

    # market currently has the best bid/ask on the April 9th expiration 60000 call:
    # bid: 2105, ask: 2360 -- so the bot would want to place a sell order at 2359, and walk it down, even selling to the
    # 2015 bid gives a theoretical edge of 2015-1869 = $146, but we'd much rather get filled closer to the ask, say
    # we get filled for 100 contracts at 2350-1869 = $481

    # ... and the put
    # bid: 2500, ask: 2800, since the market is pricing puts under the theoretical $2863
    # the bot would want to place a bid
    # 2501 (2863-2501 = $362 theoretical edge) -- this is all making the assumption that the 71% volatility is right.


if __name__ == "__main__":
    vol_example()
