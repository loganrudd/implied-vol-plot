from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_lets_be_rational.exceptions import BelowIntrinsicException, AboveMaximumException
import numpy as np
# http://www.vollib.org/documentation/python/1.0.2/apidoc/py_vollib.black_scholes.html

# Risk free interest rate 0.5%
interest = 0.005


def get_vol(attrs):
    option_price = attrs['price']
    ul_price = attrs['ul_price']
    dte = attrs['dte']
    strike = attrs['strike']
    flag = attrs['flag']
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
    price = black_scholes(flag, ul_price, strike, dte/365, interest, iv)
    return price


def vol_example():
    ul_price = 60200
    strike = 60000
    dte = 4.5
    option_price_mid = 2200

    iv = implied_volatility(option_price_mid, ul_price, strike, dte/365, interest, 'p')
    print(f'Put iv:{iv}')


if __name__ == "__main__":
    vol_example()
