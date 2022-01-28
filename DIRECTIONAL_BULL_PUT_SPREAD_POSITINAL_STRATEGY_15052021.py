from urllib.request import urlopen
import urllib
import time
import pandas as pd
import numpy as np
import requests
import datetime
from time import sleep
from jugaad_trader import Zerodha
from os import system
import indicators_ds
import talib
import telegram
import logging


pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 1000)

logging.basicConfig(filename="D:\\ALGO TRADING\\LIVE PROJECTS\\LIVE TRADINGS\\OTHER OPTION STRATEGIES\\BEAR & BULL PUT SPREAD\\bear_bull_strategy_log_file.log",
                    format='%(asctime)s: %(lineno)d: %(message)s: %(funcName)s', filemode='a', level=logging.DEBUG)

logger = logging.getLogger()

token = '1745110167:AAEoSJVeKQ3XTPeu6TVVVGI46EMQ0z4eYAs'
chat_id = '765380639'

bot = telegram.Bot(token)


class OMS():

    def __init__(self,):
        # initialize zerodha access_token
        self.kite = Zerodha()
        self.kite.set_access_token()
        # check if ltp is coming in from zerodha api, else generate access token
        try:
            self.kite.ltp(['NSE:MARUTI'])
        except:
            logger.critical("Internet is down")
            # !jtrader zerodha startsession
            system('jtrader zerodha startsession')
            self.kite.set_access_token()

        self.master_contract = self.get_master_contract()

    def reset_access_token(self):

        system('jtrader zerodha startsession')
        self.kite.set_access_token()

    def get_master_contract(self):
        try:
            response = requests.get('http://api.kite.trade/instruments')
            response_text = response.text
            response_text = response_text.split('\n')
            master_contract = pd.DataFrame(list(map(lambda x: x.split(','), response_text)))
            master_contract.columns = master_contract.loc[0].values
            master_contract = master_contract.iloc[1:]
            master_contract = master_contract[master_contract['tradingsymbol'].apply(
                lambda x: x is not None)]
            master_contract['instrument_token'] = master_contract['instrument_token'].apply(int)
            master_contract['expiry'] = master_contract[master_contract['expiry'] != '']['expiry'].apply(
                lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date())
            master_contract['strike'] = master_contract['strike'].apply(float)
            master_contract['name'] = master_contract['name'].apply(lambda x: str(x)[1:-1])
            master_contract.sort_values(by='expiry', inplace=True)
            return master_contract
        except Exception as e:
            logger.error(f"Could not get master contract and error is: {e}")
            raise ValueError(f"Could not get master contract :: {e}")

    def get_index_symbol_for_zerodha(self, instrument_name='NIFTY 50'):

        instrument_name = instrument_name.upper()
        df_zerodha_symbols = self.get_master_contract()
        ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['name'] == instrument_name) & (
            df_zerodha_symbols['segment'] == 'INDICES')]['tradingsymbol'].iloc[0]

        return (f"NSE:{ticker_symbol}", ticker_symbol)

    def get_equity_symbol_for_zerodha(self, instrument_name='ACC'):

        instrument_name = instrument_name.upper().strip()

        df_zerodha_symbols = self.get_master_contract()

        ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['name'] == instrument_name) & (
            df_zerodha_symbols['segment'] == 'NSE')]['tradingsymbol'].iloc[0]

        return (f"NSE:{ticker_symbol}", ticker_symbol)

    def get_NFO_symbol_for_zerodha(self, instrument_name='nifty', instrument_type='future', expiry_type='near', expiry_status='monthly', option_type='CE', strike_price=None):

        df_zerodha_symbols = self.get_master_contract()
        instrument_name = instrument_name.upper().strip()
        instrument_type = instrument_type.lower().strip()
        expiry_type = expiry_type.lower().strip()
        option_type = option_type.upper().strip()
        expiry_status = expiry_status.lower().strip()

        if (instrument_type == 'future'):

            if expiry_type == 'near':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[1]

            elif expiry_type == 'far':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[2]

        elif (instrument_type == 'option') and (expiry_status == 'weekly'):

            if expiry_type == 'near':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[1]

            elif expiry_type == 'far':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[2]

        elif (instrument_type == 'option') and (expiry_status == 'monthly'):

            if expiry_type == 'near':
                monthly_expiry_date = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['expiry'].iloc[0]

                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price) & (df_zerodha_symbols['expiry'] == monthly_expiry_date)]['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':

                monthly_expiry_date = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['expiry'].iloc[1]

                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price) & (df_zerodha_symbols['expiry'] == monthly_expiry_date)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'far':

                monthly_expiry_date = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['expiry'].iloc[2]

                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'NFO-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price) & (df_zerodha_symbols['expiry'] == monthly_expiry_date)]['tradingsymbol'].iloc[0]

        return (f"NFO:{ticker_symbol}", ticker_symbol)

    def get_forex_symbol_for_zerodha(self, instrument_name='usdinr', instrument_type='future', expiry_type='near', option_type='CE', strike_price=None):

        instrument_name = instrument_name.upper().strip()
        instrument_type = instrument_type.lower().strip()
        expiry_type = expiry_type.lower().strip()
        option_type = option_type.upper().strip()

        df_zerodha_symbols = self.get_master_contract()

        if instrument_type == 'future':

            if expiry_type == 'near':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[1]

            elif expiry_type == 'far':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[2]

        elif instrument_type == 'option':

            if expiry_type == 'near':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[1]

            elif expiry_type == 'far':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'CDS-OPT') & (df_zerodha_symbols['name'] == instrument_name) & (
                    df_zerodha_symbols['instrument_type'] == option_type) & (df_zerodha_symbols['strike'] == strike_price)].sort_values(by='expiry')['tradingsymbol'].iloc[2]

        return (f"CDS:{ticker_symbol}", ticker_symbol)

    def get_commodity_symbol_for_zerodha(self, instrument_name='Goldpetal', instrument_type='future', expiry_type='near'):

        instrument_name = instrument_name.upper().strip()
        instrument_type = instrument_type.lower().strip()
        expiry_type = expiry_type.lower().strip()

        df_zerodha_symbols = self.get_master_contract()

        if instrument_type == 'future':

            if expiry_type == 'near':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'MCX-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[0]

            elif expiry_type == 'next':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'MCX-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[1]

            elif expiry_type == 'far':
                ticker_symbol = df_zerodha_symbols[(df_zerodha_symbols['segment'] == 'MCX-FUT') & (
                    df_zerodha_symbols['name'] == instrument_name)].sort_values(by='expiry')['tradingsymbol'].iloc[2]

        return (f"MCX:{ticker_symbol}", ticker_symbol)

    def fno_quantity_per_lot(self, instrument_name='NIFTY', segment='INDICES'):

        instrument_name = instrument_name.upper().strip()

        if segment == 'NFO-OPT' or segment == 'NFO-FUT' or segment == 'INDICES':
            quantity_per_lot = self.master_contract[self.master_contract['name']
                                                    == instrument_name]['lot_size'].iloc[0]
        else:
            quantity_per_lot = 1

        return quantity_per_lot

    def get_ltp(self, instruments_name_with_exchange):

        count = 0
        while True:

            try:

                ltp = self.kite.ltp(instruments_name_with_exchange)[
                    instruments_name_with_exchange]['last_price']

                return ltp

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    ltp = self.kite.ltp(instruments_name_with_exchange)[
                        instruments_name_with_exchange]['last_price']
                    return ltp

    def get_instrument_token(self, instruments_name_with_exchange):

        count = 0
        while True:

            try:
                instruments_token = self.kite.ltp(instruments_name_with_exchange)[
                    instruments_name_with_exchange]['instrument_token']
                return instruments_token

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    instruments_token = self.kite.ltp(instruments_name_with_exchange)[
                        instruments_name_with_exchange]['instrument_token']
                    return instruments_token

    def get_available_margins(self, segment=None):

        available_margin_equity = pd.DataFrame(self.kite.margins()).T['available']['equity']
        available_margin_commodity = pd.DataFrame(self.kite.margins()).T['available']['commodity']
        self.available_margin_df = pd.DataFrame(available_margin_equity, index=range(1)).T
        self.available_margin_df.columns = ['equity']
        self.available_margin_df['commodity'] = pd.DataFrame(
            available_margin_commodity, index=range(1)).T

        return self.available_margin_df

    def get_utilised_margins(self, segment=None):

        utilised_margin_equity = pd.DataFrame(self.kite.margins()).T['utilised']['equity']
        utilised_margin_commodity = pd.DataFrame(self.kite.margins()).T['utilised']['commodity']
        self.utilised_margin_df = pd.DataFrame(utilised_margin_equity, index=range(1)).T
        self.utilised_margin_df.columns = ['equity']
        self.utilised_margin_df['commodity'] = pd.DataFrame(
            utilised_margin_commodity, index=range(1)).T

        return self.utilised_margin_df

    def get_ohlc(self, trading_symbol_with_exchange):

        count = 0
        while True:

            try:
                return pd.DataFrame(self.kite.ohlc(self, trading_symbol_with_exchange)[trading_symbol_with_exchange]['ohlc'], index=range(1))

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(self.kite.ohlc(self, trading_symbol_with_exchange)[trading_symbol_with_exchange]['ohlc'], index=range(1))

    def get_profile(self):

        return self.kite.profile()

    def get_quote(self, trading_symbol_with_exchange):

        count = 0
        while True:

            try:

                buy_side = pd.DataFrame(self.kite.quote(self, trading_symbol_with_exchange)[
                                        trading_symbol_with_exchange]['depth']['buy'])

                buy_side.columns = ['buy_price', 'buy_quantity', 'buy_orders']
                sell_side = pd.DataFrame(self.kite.quote(self, trading_symbol_with_exchange)[
                                         trading_symbol_with_exchange]['depth']['sell'])

                sell_side.columns = ['sell_price', 'sell_quantity', 'sell_orders']

                self.bid_ask_quote = pd.concat([buy_side, sell_side], axis=1)

                return self.bid_ask_quote

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    buy_side = pd.DataFrame(self.kite.quote(self, trading_symbol_with_exchange)[
                                            trading_symbol_with_exchange]['depth']['buy'])

                    buy_side.columns = ['buy_price', 'buy_quantity', 'buy_orders']
                    sell_side = pd.DataFrame(self.kite.quote(self, trading_symbol_with_exchange)[
                                             trading_symbol_with_exchange]['depth']['sell'])

                    sell_side.columns = ['sell_price', 'sell_quantity', 'sell_orders']

                    self.bid_ask_quote = pd.concat([buy_side, sell_side], axis=1)
                    return self.bid_ask_quote

    def get_historical_data(self, instruments_name_with_exchange, days=5, interval='15minute'):

        count = 0
        while True:

            try:

                instrument_token = self.get_instrument_token(instruments_name_with_exchange)

                from_date = datetime.datetime.today() - datetime.timedelta(days=days)
                to_date = datetime.datetime.now()

                return pd.DataFrame(self.kite.historical_data(instrument_token, from_date, to_date, interval))

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    instrument_token = self.get_instrument_token(instruments_name_with_exchange)

                    from_date = datetime.datetime.today() - datetime.timedelta(days=days)
                    to_date = datetime.datetime.now()

                    return pd.DataFrame(self.kite.historical_data(instrument_token, from_date, to_date, interval))

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None):
        '''
        variety: 'regular', 'amo', 'bo', 'co'
        tradingsymbol: Tradingsymbol of the instrument
        transaction_type: BUY or SELL
        product: 'CNC', 'NRML', 'MIS'
        order_type: 'MARKET', 'LIMIT'

        trigger_price will be used for stoploss

        squareoff	Price difference at which the order should be squared off and profit booked (eg: Order price is 100. Profit target is 102. So squareoff = 2)

        '''

        return self.kite.place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)

    def place_market_order(self, exchange, tradingsymbol, transaction_type, quantity, product):

        if exchange == 'NFO':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

        elif exchange == 'MCX':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

        elif exchange == 'NSE':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

        elif exchange == 'CDS':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

        count = 0
        while True:

            try:
                self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                      tradingsymbol=tradingsymbol,
                                                      exchange=exchange,
                                                      transaction_type=transaction_type,
                                                      quantity=quantity,
                                                      order_type=self.kite.ORDER_TYPE_MARKET,
                                                      product=product)

                return self.entry_id

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                          tradingsymbol=tradingsymbol,
                                                          exchange=exchange,
                                                          transaction_type=transaction_type,
                                                          quantity=quantity,
                                                          order_type=self.kite.ORDER_TYPE_MARKET,
                                                          product=product)
                    return self.entry_id

    def place_limit_order(self, exchange, tradingsymbol, transaction_type, quantity, product, price=None):

        if exchange == 'NFO':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

        elif exchange == 'MCX':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

        elif exchange == 'NSE':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

        elif exchange == 'CDS':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

        count = 0
        while True:

            try:

                self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                      tradingsymbol=tradingsymbol,
                                                      exchange=exchange,
                                                      transaction_type=transaction_type,
                                                      quantity=quantity,
                                                      price=price,
                                                      order_type=self.kite.ORDER_TYPE_LIMIT,
                                                      product=product)

                return self.entry_id

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                          tradingsymbol=tradingsymbol,
                                                          exchange=exchange,
                                                          transaction_type=transaction_type,
                                                          quantity=quantity,
                                                          price=price,
                                                          order_type=self.kite.ORDER_TYPE_LIMIT,
                                                          product=product)
                    return self.entry_id

    def place_stoploss_limit_order(self, exchange, tradingsymbol, transaction_type, quantity, product, trigger_price=None, price=None):

        if exchange == 'NFO':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

        elif exchange == 'MCX':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

        elif exchange == 'NSE':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

        elif exchange == 'CDS':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

        count = 0
        while True:

            try:

                self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                      tradingsymbol=tradingsymbol,
                                                      exchange=exchange,
                                                      transaction_type=transaction_type,
                                                      quantity=quantity,
                                                      trigger_price=trigger_price,
                                                      price=price,
                                                      order_type=self.kite.ORDER_TYPE_LIMIT,
                                                      product=product)

                return self.entry_id

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                          tradingsymbol=tradingsymbol,
                                                          exchange=exchange,
                                                          transaction_type=transaction_type,
                                                          quantity=quantity,
                                                          trigger_price=trigger_price,
                                                          price=price,
                                                          order_type=self.kite.ORDER_TYPE_LIMIT,
                                                          product=product)
                    return self.entry_id

    def place_stoploss_market_order(self, exchange, tradingsymbol, transaction_type, quantity, product, trigger_price=None):

        if exchange == 'NFO':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NFO

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NFO

        elif exchange == 'MCX':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_MCX

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_MCX

        elif exchange == 'NSE':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_NSE

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_NSE

        elif exchange == 'CDS':

            if product == 'MIS':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_MIS
                    exchange = self.kite.EXCHANGE_CDS

            elif product == 'NRML':

                if transaction_type == 'BUY':

                    transaction_type = self.kite.TRANSACTION_TYPE_BUY
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

                elif transaction_type == 'SELL':

                    transaction_type = self.kite.TRANSACTION_TYPE_SELL
                    product = self.kite.PRODUCT_NRML
                    exchange = self.kite.EXCHANGE_CDS

        count = 0
        while True:

            try:
                self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                      tradingsymbol=tradingsymbol,
                                                      exchange=exchange,
                                                      transaction_type=transaction_type,
                                                      quantity=quantity,
                                                      trigger_price=trigger_price,
                                                      order_type=self.kite.ORDER_TYPE_SLM,
                                                      product=product)

                return self.entry_id

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    self.entry_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                          tradingsymbol=tradingsymbol,
                                                          exchange=exchange,
                                                          transaction_type=transaction_type,
                                                          quantity=quantity,
                                                          trigger_price=trigger_price,
                                                          order_type=self.kite.ORDER_TYPE_SLM,
                                                          product=product)

                    return self.entry_id

    def get_order_history(self, order_id):

        count = 0
        while True:

            try:
                return pd.DataFrame(self.kite.order_history(order_id))

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(self.kite.order_history(order_id))

    def get_order_trades(self, order_id):
        '''
        This fucntion will be used to findout the quantity placed order.

        '''

        count = 0
        while True:
            try:
                return pd.DataFrame(self.kite.order_trades(order_id))

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(self.kite.order_trades(order_id))

    def get_order(self):

        count = 0
        while True:

            try:
                return pd.DataFrame(self.kite.orders())

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(self.kite.orders())

    def get_positions_net(self):

        count = 0
        while True:

            try:

                net_dict = self.kite.positions()['net']
                net_list = []
                for net in net_dict:
                    net_list.append(net)

                return pd.DataFrame(net_list)

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(net_list)

    def get_positions_day(self):

        count = 0
        while True:

            try:

                day_dict = self.kite.positions()['day']

                day_list = []

                for day in day_dict:

                    day_list.append(day)

                return pd.DataFrame(day_list)

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(day_list)

    def get_trades(self):

        count = 0
        while True:

            try:
                return pd.DataFrame(self.kite.trades())

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return pd.DataFrame(self.kite.trades())

    def get_cancel_order(self, order_id):

        count = 0
        while True:

            try:
                return self.kite.cancel_order(variety='regular', order_id=order_id, parent_order_id=None)
                break

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return self.kite.cancel_order(variety='regular', order_id=order_id, parent_order_id=None)

    def get_exit_order(self, order_id):

        count = 0
        while True:
            try:
                return self.kite.exit_order(order_id, parent_order_id=None)
                break

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return self.kite.exit_order(order_id, parent_order_id=None)

    def get_holdings(self):

        count = 0
        while True:
            try:
                return self.kite.holdings(self)
                break

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return self.kite.holdings(self)

    def place_modify_limit_order(self, order_id, variety='regular', quantity=None, price=None, order_type=None):

        count = 0
        while True:
            try:
                return self.kite.modify_order(variety=variety, order_id=order_id, quantity=None, price=None, order_type=None)

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return self.kite.modify_order(variety=variety, order_id=order_id, quantity=None, price=None, order_type=None)

    def place_modify_market_order(self, order_id, variety='regular', quantity=None):

        count = 0
        while True:
            try:
                return self.kite.modify_order(variety=variety, order_id=order_id, quantity=None, price=None, order_type=self.kite.ORDER_TYPE_MARKET)

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return self.kite.modify_order(variety=variety, order_id=order_id, quantity=None, price=None, order_type=self.kite.ORDER_TYPE_MARKET)

    def close_all_open_positions(self):

        count = 0
        while True:
            try:

                positions = self.kite.positions()['net']
                for x in range(len(positions)):
                    if abs(positions[x]['quantity']) > 0:
                        tradingsymbol = positions[x]['tradingsymbol']
                        quantity = positions[x]['quantity']
                        product = positions[x]['product']
                        exchange = positions[x]['exchange']

                        if quantity < 0:
                            exit_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                            tradingsymbol=tradingsymbol,
                                                            exchange=exchange,
                                                            transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                                                            quantity=quantity,
                                                            order_type=self.kite.ORDER_TYPE_MARKET,
                                                            product=product)
                        elif quantity > 0:
                            exit_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR,
                                                            tradingsymbol=tradingsymbol,
                                                            exchange=exchange,
                                                            transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                                                            quantity=abs(quantity),
                                                            order_type=self.kite.ORDER_TYPE_MARKET,
                                                            product=product)
                        else:
                            pass

            except:
                self.reset_access_token()
                count += 1
                if count == 2:
                    return exit_id

    def except_function(self):

        count = 0
        while count <= 3:
            try:

                self.kite.ltp(['NSE:MARUTI'])
                break

            except:
                self.reset_access_token()
                count += 1

            if count == 3:
                break

        if count == 0:
            print('No internet issue')
            print()

            bot.send_message(chat_id=chat_id, text='No internet issue',
                             disable_web_page_preview=True, disable_notification=True)

        elif count > 0 and count < 3:
            print('Internet issue is resolved')
            print()

            bot.send_message(chat_id=chat_id, text='Internet issue is resolved',
                             disable_web_page_preview=True, disable_notification=True)

        elif count == 3:
            print("Internet issue... check karo bhai...")
            print()

            bot.send_message(chat_id=chat_id, text="Internet issue... check karo bhai...",
                             disable_web_page_preview=True, disable_notification=True)

        return count


obj_oms = OMS()


class StrategyExecution():

    def __init__(self, exchange='NFO', underlying='NIFTY', instrument_type='option', expiry_status='weekly', segment='NFO-OPT', option_type=None, strike_price=None, lots=1, rsi_fast=5, rsi_slow=14, data_days=3, data_interval='hourly'):
        """
        Exchange: NSE, NFO, CDS, MCX

        Segment: NFO-OPT, CDS-OPT
        """
        logger.info("Execution has been started...")

        self.exchange = exchange
        self.underlying = underlying.upper()
        self.instrument_type = instrument_type
        self.expiry_status = expiry_status
        self.segment = segment
        self.option_type = option_type
        self.strike_price = strike_price
        self.lots = lots
        self.rsi_fast = rsi_fast
        self.rsi_slow = rsi_slow
        self.data_days = data_days
        self.data_interval = data_interval
        self.obj_oms = OMS()

        contracts = self.obj_oms.get_master_contract()
        expiry_date = contracts[(contracts['name'] == self.underlying) & (
            contracts['segment'] == self.segment)].sort_values('expiry')['expiry'].iloc[0]

        if (expiry_date - datetime.date.today()).days <= 1:
            self.expiry_type = 'next'
        else:
            self.expiry_type = 'near'

        base_list = sorted(abs(contracts[(contracts['name'] == self.underlying) & (
            contracts['segment'] == self.segment) & (contracts['instrument_type'] == 'CE')]['strike'].diff()))

        filter_base_list = []

        for _ in base_list:
            if (_ != 0.0) and (_ != np.nan):
                filter_base_list.append(_)

        self.base = filter_base_list[1]

        self.total_quantity = int(self.obj_oms.fno_quantity_per_lot(
            instrument_name=self.underlying, segment=self.segment))*self.lots

        if self.underlying == 'USDINR':
            self.tick_size = 0.0025

        else:
            self.tick_size = 0.05

        if (self.exchange == 'NSE') or (self.exchange == 'NFO'):
            self.start_time = datetime.time(9, 15)
            self.end_time = datetime.time(15, 30)
            # self.end_time = datetime.time(hour=23, minute=30)

        elif self.exchange == 'MCX':
            self.start_time = datetime.time(9, 0)
            self.end_time = datetime.time(23, 30)

        elif self.exchange == 'CDS':
            self.start_time = datetime.time(9, 0)
            self.end_time = datetime.time(17, 30)

        strategy_entry_end_time = 15    # Strategy entry end time shall be in minutes.
        self.end_time = (datetime.datetime.combine(datetime.date(1, 1, 1), self.end_time) -
                         datetime.timedelta(minutes=strategy_entry_end_time)).time()

        try:
            self.trade_log_df = pd.read_pickle(
                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')

        except:
            print('entered in except for log df')
            self.trade_log_df = pd.DataFrame()
            self.trade_log_df.to_pickle(
                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')

            logger.info("As no trade_log_df was present, new dataframe has been created.")

        try:

            # state df used for current posisition status, current order status, current signal status

            self.state_df = pd.read_pickle(
                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

            # self.long_strategy_signal = ''
            # self.short_strategy_signal = ''
            print(self.state_df)

            self.long_strategy_long_position = self.state_df['long_strategy_long_position_status'].iloc[0]
            self.short_strategy_long_position = self.state_df['short_strategy_long_position_status'].iloc[0]
            # position used for flag,
            self.long_strategy_short_position = self.state_df['long_strategy_short_position_status'].iloc[0]
            self.short_strategy_short_position = self.state_df['short_strategy_short_position_status'].iloc[0]

            self.long_strategy_signal = self.state_df['long_strategy_signal_status'].iloc[0]
            # signal_status are long, short
            self.short_strategy_signal = self.state_df['short_strategy_signal_status'].iloc[0]
            # order_status are 'Non complete' and 'complete'. (open_order = 1 for pending, 0 for complete and rejected.)
            self.long_strategy_position = self.state_df['long_strategy_position'].iloc[0]
            self.short_strategy_position = self.state_df['short_strategy_position'].iloc[0]
            self.long_strategy_long_open_order = self.state_df['long_strategy_long_order_status'].iloc[0]
            self.short_strategy_long_open_order = self.state_df['short_strategy_long_order_status'].iloc[0]
            self.long_strategy_short_open_order = self.state_df['long_strategy_short_order_status'].iloc[0]
            self.short_strategy_short_open_order = self.state_df['short_strategy_short_order_status'].iloc[0]

            self.long_strategy_leg_trading_symbol_long = self.state_df['long_strategy_long_option_symbol'].iloc[0]

            self.long_strategy_leg_option_trading_symbol_with_exchange_long = self.state_df[
                'long_strategy_long_option_symbol_with_exchange'].iloc[0]

            self.long_strategy_leg_trading_symbol_short = self.state_df['long_strategy_short_option_symbol'].iloc[0]

            self.long_strategy_leg_option_trading_symbol_with_exchange_short = self.state_df[
                'long_strategy_short_option_symbol_with_exchange'].iloc[0]

            self.short_strategy_leg_trading_symbol_long = self.state_df['short_strategy_long_option_symbol'].iloc[0]

            self.short_strategy_leg_option_trading_symbol_with_exchange_long = self.state_df[
                'short_strategy_long_option_symbol_with_exchange'].iloc[0]

            self.short_strategy_leg_trading_symbol_short = self.state_df[
                'short_strategy_short_option_symbol'].iloc[0]

            self.short_strategy_leg_option_trading_symbol_with_exchange_short = self.state_df[
                'short_strategy_short_option_symbol_with_exchange'].iloc[0]

        except Exception as e:

            print('making new state df')

            print(e)

            self.state_df = pd.DataFrame(
                columns=['long_strategy_long_position_status', 'long_strategy_short_position_status', 'short_strategy_long_position_status', 'short_strategy_short_position_status', 'long_strategy_signal_status', 'short_strategy_signal_status', 'long_strategy_long_order_status', 'long_strategy_short_order_status', 'short_strategy_long_order_status', 'short_strategy_short_order_status', 'long_strategy_long_option_symbol', 'long_strategy_short_option_symbol', 'short_strategy_long_option_symbol', 'short_strategy_short_option_symbol', 'long_strategy_position', 'short_strategy_position', 'long_strategy_order_id_long_option', 'short_strategy_order_id_long_option', 'long_strategy_order_id_short_option', 'short_strategy_order_id_short_option', 'long_strategy_long_option_symbol_with_exchange', 'long_strategy_short_option_symbol_with_exchange', 'short_strategy_long_option_symbol_with_exchange', 'short_strategy_short_option_symbol_with_exchange', 'max_strategy_loss', 'max_strategy_profit', 'max_RR_ratio'])

            self.long_strategy_long_position = 0
            self.short_strategy_long_position = 0
            self.long_strategy_short_position = 0
            self.short_strategy_short_position = 0
            self.long_strategy_signal = None
            self.short_strategy_signal = None
            self.long_strategy_long_open_order = 0
            self.short_strategy_long_open_order = 0
            self.long_strategy_short_open_order = 0
            self.short_strategy_short_open_order = 0
            self.long_strategy_position = 0
            self.short_strategy_position = 0
            self.long_strategy_leg_trading_symbol_long = ''
            self.long_strategy_leg_option_trading_symbol_with_exchange_long = ''
            self.long_strategy_leg_trading_symbol_short = ''
            self.long_strategy_leg_option_trading_symbol_with_exchange_short = ''
            self.short_strategy_leg_trading_symbol_long = ''
            self.short_strategy_leg_option_trading_symbol_with_exchange_long = ''
            self.short_strategy_leg_trading_symbol_short = ''
            self.short_strategy_leg_option_trading_symbol_with_exchange_short = ''

            self.state_df.loc[0,
                              'long_strategy_long_position_status'] = self.long_strategy_long_position
            self.state_df.loc[0,
                              'short_strategy_long_position_status'] = self.short_strategy_long_position
            self.state_df.loc[0,
                              'long_strategy_short_position_status'] = self.long_strategy_short_position
            self.state_df.loc[0,
                              'short_strategy_short_position_status'] = self.short_strategy_short_position
            self.state_df.loc[0, 'long_strategy_signal_status'] = self.long_strategy_signal
            self.state_df.loc[0, 'short_strategy_signal_status'] = self.short_strategy_signal
            self.state_df.loc[0,
                              'long_strategy_long_order_status'] = self.long_strategy_long_open_order
            self.state_df.loc[0,
                              'short_strategy_long_order_status'] = self.short_strategy_long_open_order
            self.state_df.loc[0,
                              'long_strategy_short_order_status'] = self.long_strategy_short_open_order
            self.state_df.loc[0,
                              'short_strategy_short_order_status'] = self.short_strategy_short_open_order
            self.state_df.loc[0, 'long_strategy_position'] = self.long_strategy_position
            self.state_df.loc[0, 'short_strategy_position'] = self.short_strategy_position
            self.state_df.loc[0, 'long_strategy_long_option_symbol'] = self.long_strategy_leg_trading_symbol_long
            self.state_df.loc[0, 'long_strategy_long_option_symbol_with_exchange'] = self.long_strategy_leg_option_trading_symbol_with_exchange_long
            self.state_df.loc[0, 'long_strategy_short_option_symbol'] = self.long_strategy_leg_trading_symbol_short
            self.state_df.loc[0, 'long_strategy_short_option_symbol_with_exchange'] = self.long_strategy_leg_option_trading_symbol_with_exchange_short
            self.state_df.loc[0, 'short_strategy_long_option_symbol'] = self.short_strategy_leg_trading_symbol_long
            self.state_df.loc[0, 'short_strategy_long_option_symbol_with_exchange'] = self.short_strategy_leg_option_trading_symbol_with_exchange_long
            self.state_df.loc[0, 'short_strategy_short_option_symbol'] = self.short_strategy_leg_trading_symbol_short
            self.state_df.loc[0, 'short_strategy_short_option_symbol_with_exchange'] = self.short_strategy_leg_option_trading_symbol_with_exchange_short

            logger.info("As no state_df was present, new dataframe has been created.")

    def get_historical_data(self):

        self.get_spot_leg_trading_symbol()

        self.price_data = pd.DataFrame(self.obj_oms.get_historical_data(
            instruments_name_with_exchange=self.spot_trading_symbol_with_exchange, days=self.data_days, interval=self.data_interval))

    def put_rsi(self):

        self.price_data[f'rsi_{self.rsi_fast}'] = talib.RSI(
            self.price_data['close'], timeperiod=self.rsi_fast)
        self.price_data[f'rsi_{self.rsi_slow}'] = talib.RSI(
            self.price_data['close'], timeperiod=self.rsi_slow)

        self.price_data.dropna(inplace=True)

    def generate_signal(self):
        '''
        Double Decker Strategy:

        if (columns['RSI_5'] >= 70) & (columns['RSI_14'] >= 50): status['traded'] = 'LONG'
        if (columns['RSI_5'] <= 30) & (columns['RSI_14'] <= 50): status['traded'] = 'SHORT'
        elif (status['traded'] == 'LONG') & (columns['RSI_5'] < 55): Exit from long trade
        elif (status['traded'] == 'SHORT') & (columns['RSI_5'] > 35): Exit from short trade

        '''

        if datetime.datetime.now().time() >= self.start_time and datetime.datetime.now().time() < self.end_time:

            print('Entered first if')
            # check supertrend status
            signal_row = self.price_data.iloc[-2]

            if (self.long_strategy_signal != 'long_entry') and (signal_row[f'rsi_{self.rsi_fast}'] >= 70) and (signal_row[f'rsi_{self.rsi_slow}'] >= 50) and (datetime.datetime.now().time() < self.end_time):

                self.long_strategy_signal = 'long_entry'

                logger.info("signal starts for long entry...")

            elif (self.long_strategy_signal == 'long_entry') and (signal_row[f'rsi_{self.rsi_fast}'] < 55):

                self.long_strategy_signal = 'long_exit'

                logger.info("signal ends for long entry...")

            if (self.short_strategy_signal != 'short_entry') and (signal_row[f'rsi_{self.rsi_fast}'] <= 30) and (signal_row[f'rsi_{self.rsi_slow}'] <= 50) and (datetime.datetime.now().time() < self.end_time):

                print('Entered short entry if')
                self.short_strategy_signal = 'short_entry'

                logger.info("signal starts for short entry...")

            elif (self.short_strategy_signal == 'short_entry') and (signal_row[f'rsi_{self.rsi_fast}'] > 35):

                self.short_strategy_signal = 'short_exit'

                logger.info("signal ends for short entry...")

        else:

            print('Signal is none...')
            self.long_strategy_signal = None
            self.short_strategy_signal = None

        self.state_df.loc[0, 'long_strategy_signal_status'] = self.long_strategy_signal
        print('Signal for long strategy is: ', self.long_strategy_signal)

        self.state_df.loc[0, 'short_strategy_signal_status'] = self.short_strategy_signal
        print('Signal for short stratey is: ', self.short_strategy_signal)

        self.state_df.to_pickle(
            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

    def get_spot_leg_trading_symbol(self):

        if self.underlying == 'NIFTY':

            self.spot_trading_symbol_with_exchange = self.obj_oms.get_index_symbol_for_zerodha(
                instrument_name='NIFTY 50')[0]
            self.spot_trading_symbol = self.obj_oms.get_index_symbol_for_zerodha(instrument_name='NIFTY 50')[
                1]
            self.spot_instrument_token = self.obj_oms.get_instrument_token(
                instruments_name_with_exchange=self.spot_trading_symbol_with_exchange)

            logger.info("spot_trading_symbol for NIFTY has been called...")

        elif self.underlying == 'BANKNIFTY':
            self.spot_trading_symbol_with_exchange = self.obj_oms.get_index_symbol_for_zerodha(
                instrument_name='NIFTY BANK')[0]
            self.spot_trading_symbol = self.obj_oms.get_index_symbol_for_zerodha(
                instrument_name='NIFTY BANK')[1]
            self.spot_instrument_token = self.obj_oms.get_instrument_token(
                instruments_name_with_exchange=self.spot_trading_symbol_with_exchange)

            logger.info("spot_trading_symbol for BANKNIFTY has been called...")

        elif self.segment == 'CDS-OPT':

            self.spot_trading_symbol_with_exchange = self.obj_oms.get_forex_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, option_type=option_type, strike_price=self.strike_price)[0]

            self.spot_trading_symbol = self.obj_oms.get_forex_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, option_type=option_type, strike_price=self.strike_price)[1]

            self.spot_instrument_token = self.obj_oms.get_instrument_token(
                spot_trading_symbol_with_exchange)

            logger.info("spot_trading_symbol for CDS-OPT has been called...")

        else:

            self.spot_trading_symbol_with_exchange = self.obj_oms.get_equity_symbol_for_zerodha(
                self, instrument_name=self.underlying)[0]

            self.spot_trading_symbol = self.obj_oms.self.obj_oms.get_equity_symbol_for_zerodha(
                self, instrument_name=self.underlying)[1]

            self.spot_instrument_token = self.obj_oms.get_instrument_token(
                spot_trading_symbol_with_exchange)

            logger.info("spot_trading_symbol for stocks has been called...")

    def get_option_leg_trading_symbol(self, option_type=None, strike_price=None):

        if self.segment == 'NFO-OPT':

            option_trading_symbol_with_exchange = self.obj_oms.get_NFO_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, expiry_status=self.expiry_status, option_type=option_type, strike_price=strike_price)[0]

            option_trading_symbol = self.obj_oms.get_NFO_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, expiry_status=self.expiry_status, option_type=option_type, strike_price=strike_price)[1]

            option_instrument_token = self.obj_oms.get_instrument_token(
                option_trading_symbol_with_exchange)

        elif self.segment == 'CDS-OPT':

            option_trading_symbol_with_exchange = self.obj_oms.get_NFO_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, expiry_status=self.expiry_status, option_type=option_type, strike_price=self.strike_price)[0]

            option_trading_symbol = self.obj_oms.get_NFO_symbol_for_zerodha(
                instrument_name=self.underlying, instrument_type=self.instrument_type, expiry_type=self.expiry_type, expiry_status=self.expiry_status, option_type=option_type, strike_price=self.strike_price)[1]

            option_instrument_token = self.obj_oms.get_instrument_token(
                option_trading_symbol_with_exchange)

        return option_trading_symbol_with_exchange, option_trading_symbol, option_instrument_token

    def get_option_trading_symbols(self):

        ltp = self.obj_oms.get_ltp(
            instruments_name_with_exchange=self.spot_trading_symbol_with_exchange)
        atm = round(ltp/self.base) * self.base

        if self.long_strategy_signal == 'long_entry':
            self.long_strategy_leg_option_trading_symbol_with_exchange_long, self.long_strategy_leg_trading_symbol_long, self.long_strategy_leg_option_instrument_token_long = self.get_option_leg_trading_symbol(
                option_type='PE', strike_price=atm + (self.base * 4))
            self.long_strategy_leg_option_trading_symbol_with_exchange_short, self.long_strategy_leg_trading_symbol_short, self.long_strategy_leg_option_instrument_token_short = self.get_option_leg_trading_symbol(
                option_type='PE', strike_price=atm + (self.base * 6))

        if self.short_strategy_signal == 'short_entry':
            self.short_strategy_leg_option_trading_symbol_with_exchange_long, self.short_strategy_leg_trading_symbol_long, self.short_strategy_leg_option_instrument_token_long = self.get_option_leg_trading_symbol(
                option_type='PE', strike_price=atm - (self.base * 4))
            self.short_strategy_leg_option_trading_symbol_with_exchange_short, self.short_strategy_leg_trading_symbol_short, self.short_strategy_leg_option_instrument_token_short = self.get_option_leg_trading_symbol(
                option_type='PE', strike_price=atm - (self.base * 6))

        logger.info("Options leg trading_symbol has been called...")

    def place_option_limit_order_for_entry(self, order_type, exchange_symbol, trading_symbol, signal):

        limit_order_complete = 0

        open_order = 0

        while limit_order_complete == 0:

            try:
                if order_type == 'BUY':
                    leg_price = self.obj_oms.get_quote(exchange_symbol).iloc[0]['buy_price']

                    print(
                        f'Long_leg_price in first attempt for leg {trading_symbol} is: ', leg_price)
                    print()

                    bot.send_message(
                        chat_id=chat_id, text=f'Long_leg_price in first attempt for leg {trading_symbol} is: {leg_price}', disable_web_page_preview=True, disable_notification=True)

                else:
                    leg_price = self.obj_oms.get_quote(exchange_symbol).iloc[0]['sell_price']

                    print(
                        f'Short_leg_price in first attempt for leg {trading_symbol} is: ', leg_price)
                    print()

                    bot.send_message(
                        chat_id=chat_id, text=f'Short_leg_price in first attempt for leg {trading_symbol} is: {leg_price}', disable_web_page_preview=True, disable_notification=True)

                order_id = self.obj_oms.place_limit_order(
                    exchange=self.exchange, tradingsymbol=trading_symbol, transaction_type=order_type, quantity=self.total_quantity, product='NRML', price=leg_price)
                order_received_time = self.obj_oms.get_order_history(
                    order_id)['order_timestamp'].iloc[-1].time()

                print(
                    f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent')
                logger.info(
                    f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent')
                print()

                bot.send_message(chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent',
                                 disable_web_page_preview=True, disable_notification=True)

                if order_type == 'BUY' and signal == 'long_entry':
                    self.long_strategy_long_open_order = 1
                    self.state_df.loc[0,
                                      'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                    self.state_df.loc[0, 'long_strategy_long_option_symbol'] = trading_symbol
                    self.state_df.loc[0, 'long_strategy_order_id_long_option'] = order_id

                elif order_type == 'BUY' and signal == 'short_entry':
                    self.short_strategy_long_open_order = 1
                    self.state_df.loc[0,
                                      'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                    self.state_df.loc[0,
                                      'short_strategy_long_option_symbol'] = trading_symbol
                    self.state_df.loc[0, 'short_strategy_order_id_long_option'] = order_id

                elif order_type == 'SELL' and signal == 'long_entry':
                    self.long_strategy_short_open_order = 1
                    self.state_df.loc[0,
                                      'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                    self.state_df.loc[0,
                                      'long_strategy_short_option_symbol'] = trading_symbol
                    self.state_df.loc[0, 'long_strategy_order_id_short_option'] = order_id

                elif order_type == 'SELL' and signal == 'short_entry':
                    self.short_strategy_short_open_order = 1
                    self.state_df.loc[0,
                                      'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                    self.state_df.loc[0,
                                      'short_strategy_short_option_symbol'] = trading_symbol
                    self.state_df.loc[0, 'short_strategy_order_id_short_option'] = order_id

                open_order = 1

            except Exception as e:

                print(f'Error while sending {order_type} order for {trading_symbol} position: ', e)
                logger.error(
                    f'Error while sending {order_type} order for {trading_symbol} position: ', e)
                print()

                bot.send_message(
                    chat_id=chat_id, text=f'Error while sending {order_type} order for {trading_symbol} position: {e}', disable_web_page_preview=True, disable_notification=True)

                self.error = 1
                break

            if open_order == 1:

                print(f'{order_type} order for {trading_symbol} with {order_id} sent successfully')

                bot.send_message(chat_id=chat_id, text=f'{order_type} order for {trading_symbol} with {order_id} sent successfully',
                                 disable_web_page_preview=True, disable_notification=True)

                limit_order_wait_count = 0
                wait_count = 0
                while True:

                    try:
                        time.sleep(5)
                        order_status = self.obj_oms.get_order_history(order_id)['status'].iloc[-1]

                    except Exception as e:

                        print(f'Error while getting order status for order id {order_id}: ', e)
                        logger.error(
                            f'Error while getting order status for order id {order_id}: ', e)
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'Error while getting order status for order id {order_id}: {e}', disable_web_page_preview=True, disable_notification=True)

                        self.error = 1
                        break

                    if order_status == 'COMPLETE':

                        limit_order_complete = 1

                        if order_type == 'BUY' and signal == 'long_entry':
                            self.long_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                            self.long_strategy_long_position = 1
                            self.state_df.loc[0,
                                              'long_strategy_long_position_status'] = self.long_strategy_long_position

                        elif order_type == 'BUY' and signal == 'short_entry':
                            self.short_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                            self.short_strategy_long_position = 1
                            self.state_df.loc[0,
                                              'short_strategy_long_position_status'] = self.short_strategy_long_position

                        elif order_type == 'SELL' and signal == 'long_entry':
                            self.long_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                            self.long_strategy_short_position = 1
                            self.state_df.loc[0,
                                              'long_strategy_short_position_status'] = self.long_strategy_short_position

                        elif order_type == 'SELL' and signal == 'short_entry':
                            self.short_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                            self.short_strategy_short_position = 1
                            self.state_df.loc[0,
                                              'short_strategy_short_position_status'] = self.short_strategy_short_position

                        print(f'{order_type} order for {trading_symbol} with {order_id} complete')
                        logger.info(
                            f'{order_type} order for {trading_symbol} with {order_id} has been completed')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'{order_type} order for {trading_symbol} with {order_id} complete', disable_web_page_preview=True, disable_notification=True)

                        print(f'Getting {order_type} position after order execution complete')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'Getting {order_type} position after order execution complete', disable_web_page_preview=True, disable_notification=True)

                        try:

                            current_position = self.obj_oms.get_positions_net()
                            self.trade_log_df = self.trade_log_df.append(
                                current_position[current_position['tradingsymbol'] == trading_symbol])

                        except Exception as e:

                            print(f'Error while getting {trading_symbol} position: ', e)
                            logger.error(f'Error while getting {trading_symbol} position: ', e)
                            print()

                            bot.send_message(
                                chat_id=chat_id, text='Error while exiting long position due to short order being rejected: {e}', disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            break

                        self.state_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

                        self.trade_log_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')

                        break

                    elif order_status == 'REJECTED':

                        if order_type == 'BUY' and signal == 'long_entry':
                            self.long_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                            self.long_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_position_status'] = self.long_strategy_long_position
                            self.state_df.loc[0, 'long_strategy_long_option_symbol'] = ''
                            self.state_df.loc[0, 'long_strategy_order_id_long_option'] = ''

                        elif order_type == 'BUY' and signal == 'short_entry':

                            self.short_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                            self.short_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_position_status'] = self.short_strategy_long_position
                            self.state_df.loc[0,
                                              'short_strategy_long_option_symbol'] = ''
                            self.state_df.loc[0, 'short_strategy_order_id_long_option'] = ''

                        elif order_type == 'SELL' and signal == 'long_entry':

                            try:
                                exit_order_id = self.obj_oms.place_market_order(
                                    exchange=self.exchange, tradingsymbol=self.long_strategy_leg_trading_symbol_long, transaction_type='SELL', quantity=self.total_quantity, product='NRML')

                            except Exception as e:
                                print(
                                    'Error while exiting long position due to short order being rejected: ', e)

                                bot.send_message(
                                    chat_id=chat_id, text='Error while exiting long position due to short order being rejected: {e}', disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()
                                if self.error == 1:
                                    break

                            self.long_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                            self.long_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_position_status'] = self.long_strategy_long_position
                            self.long_strategy_short_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_position_status'] = self.long_strategy_short_position
                            self.state_df.loc[0,
                                              'long_strategy_short_option_symbol'] = ''
                            self.state_df.loc[0, 'long_strategy_order_id_short_option'] = ''

                            self.state_df.loc[0,
                                              'long_strategy_long_option_symbol'] = ''
                            self.state_df.loc[0, 'long_strategy_order_id_long_option'] = ''
                            self.long_strategy_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_position'] = self.long_strategy_position

                        elif order_type == 'SELL' and signal == 'short_entry':

                            try:
                                exit_order_id = self.obj_oms.place_market_order(
                                    exchange=self.exchange, tradingsymbol=self.short_strategy_leg_trading_symbol_long, transaction_type='SELL', quantity=self.total_quantity, product='NRML')

                            except Exception as e:
                                print(
                                    'Error while exiting long position due to short order being rejected: ', e)

                                bot.send_message(
                                    chat_id=chat_id, text='Error while exiting long position due to short order being rejected: {e}', disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()
                                if self.error == 1:
                                    break

                            self.short_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                            self.short_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_position_status'] = self.short_strategy_long_position
                            self.short_strategy_short_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_position_status'] = self.short_strategy_short_position
                            self.state_df.loc[0,
                                              'short_strategy_short_option_symbol'] = ''
                            self.state_df.loc[0, 'short_strategy_order_id_short_option'] = ''

                            self.state_df.loc[0,
                                              'short_strategy_short_option_symbol'] = ''
                            self.state_df.loc[0, 'short_strategy_order_id_short_option'] = ''

                            self.short_strategy_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_position'] = self.short_strategy_position

                        self.error = 1
                        limit_order_complete = 1
                        print(f'{order_type} order for {trading_symbol} rejected')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'{order_type} order for {trading_symbol} rejected', disable_web_page_preview=True, disable_notification=True)

                        print('Exit the program')
                        print()

                        bot.send_message(chat_id=chat_id, text='Exit the program',
                                         disable_web_page_preview=True, disable_notification=True)

                        logger.critical(
                            f'Order has been rejected. Please check for {order_type} order for {trading_symbol}...')

                        self.state_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                        break

                    elif order_status == 'OPEN':

                        print(
                            f'Waiting for {order_type} limit order of {trading_symbol} to complete')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'Waiting for {order_type} limit order of {trading_symbol} to complete', disable_web_page_preview=True, disable_notification=True)

                        if limit_order_wait_count == 1:

                            try:

                                leg_price_1 = self.obj_oms.get_quote(
                                    exchange_symbol).iloc[0]['buy_price']
                                leg_price_2 = self.obj_oms.get_quote(
                                    exchange_symbol).iloc[0]['sell_price']
                                number_of_ticks = round(
                                    (leg_price_2 - leg_price_1) / self.tick_size)

                                leg_price = leg_price_1 + \
                                    (round(number_of_ticks / 2) * self.tick_size)

                                print(
                                    f'Price in second attempt for leg {trading_symbol} is: ', leg_price)
                                print()

                                bot.send_message(
                                    chat_id=chat_id, text=f'Price in second attempt for leg {trading_symbol} is: {leg_price}', disable_web_page_preview=True, disable_notification=True)

                                order_id = self.obj_oms.place_modify_limit_order(
                                    order_id=order_id, price=leg_price)
                                order_received_time = self.obj_oms.get_order_history(
                                    order_id)['order_timestamp'].iloc[-1].time()

                                print(
                                    f'{order_type} limit order for leg {trading_symbol} with order id {order_id} sent')
                                print()

                                bot.send_message(
                                    chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} sent', disable_web_page_preview=True, disable_notification=True)

                            except Exception as e:

                                print(
                                    f'Error while sending modify limit order for {trading_Symbol}: ', e)
                                logger.error(
                                    f'Error while sending modify limit order for {trading_Symbol}: ', e)
                                print()

                                bot.send_message(
                                    chat_id=chat_id, text=f'Error while sending modify to market order for {trading_symbol}: {e}', disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()
                                break

                        elif limit_order_wait_count == 2:

                            try:

                                order_id = self.obj_oms.place_modify_market_order(
                                    order_id=order_id)
                                order_received_time = self.obj_oms.get_order_history(
                                    order_id)['order_timestamp'].iloc[-1].time()

                            except Exception as e:

                                print(
                                    f'Error while sending modify to market order for {trading_symbol}: ', e)
                                logger.error(
                                    f'Error while sending modify to market order for {trading_symbol}: ', e)
                                print()

                                bot.send_message(
                                    chat_id=chat_id, text=f'Error while sending modify to market order for {trading_symbol}: {e}', disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()
                                break

                        limit_order_wait_count += 1

                    else:

                        if wait_count == 0 and (datime.datetime.now().time() - order_received_time).seconds >= 60:
                            print(f'{order_type} order still pending. Order status is: ', order_status)
                            wait_count += 1

                        elif wait_count == 1 and (datime.datetime.now().time() - order_received_time).seconds >= 120:
                            print(f'{order_type} order still pending. Order status is: ', order_status)
                            wait_count += 1

                        elif wait_count == 2 and (datime.datetime.now().time() - order_received_time).seconds >= 240:
                            print(f'{order_type} order still pending. Order status is: ', order_status)
                            wait_count += 1

                        if (datime.datetime.now().time() - order_received_time).seconds >= 300:

                            print('Order still pending. Order status is: ', order_status)
                            logger.error(
                                'Order still pending after 120 seconds. Order status is: ', order_status)
                            print()

                            bot.send_message(
                                chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                            print('Exit the program')
                            print()

                            bot.send_message(chat_id=chat_id, text='Exit the program',
                                             disable_web_page_preview=True, disable_notification=True)

                            if order_type == 'BUY' and signal == 'long_entry':
                                self.long_strategy_long_position = 0
                                self.long_strategy_long_open_order = 1
                                self.state_df.loc[0,
                                                  'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                                self.state_df.loc[0,
                                                  'long_strategy_long_position_status'] = self.long_strategy_long_position

                            elif order_type == 'BUY' and signal == 'short_entry':

                                self.short_strategy_long_position = 0
                                self.short_strategy_long_open_order = 1
                                self.state_df.loc[0,
                                                  'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                                self.state_df.loc[0,
                                                  'short_strategy_long_position_status'] = self.short_strategy_long_position

                            elif order_type == 'SELL' and signal == 'long_entry':

                                self.long_strategy_short_position = 0
                                self.long_strategy_short_open_order = 1
                                self.state_df.loc[0,
                                                  'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                                self.state_df.loc[0,
                                                  'long_strategy_short_position_status'] = self.long_strategy_short_position

                            elif order_type == 'SELL' and signal == 'short_entry':

                                self.short_strategy_short_position = 0
                                self.short_strategy_short_open_order = 1
                                self.state_df.loc[0,
                                                  'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                                self.state_df.loc[0,
                                                  'short_strategy_short_position_status'] = self.short_strategy_short_position

                            limit_order_complete = 1
                            self.error = 1
                            self.state_df.to_pickle(
                                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                            break

    def place_option_market_order_for_exit(self, order_type, exchange_symbol, trading_symbol, signal):

        market_order_complete = 0
        open_order = 0

        while market_order_complete == 0:

            try:

                order_id = self.obj_oms.place_market_order(
                    exchange=self.exchange, tradingsymbol=trading_symbol, transaction_type=order_type, quantity=self.total_quantity, product='NRML')
                order_received_time = self.obj_oms.get_order_history(
                    order_id)['order_timestamp'].iloc[-1].time()

                print(f'{order_type} limit order for leg {trading_symbol} with order id {order_id} sent')
                logger.info(
                    f'{order_type} limit order for leg {trading_symbol} with order id {order_id} sent')
                print()

                bot.send_message(chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} sent',
                                 disable_web_page_preview=True, disable_notification=True)

                if order_type == 'BUY' and self.long_strategy_signal == 'long_exit':
                    self.long_strategy_long_open_order = 1
                    self.state_df.loc[0,
                                      'long_strategy_long_order_status'] = self.long_strategy_long_open_order

                elif order_type == 'SELL' and self.long_strategy_signal == 'long_exit':
                    self.long_strategy_short_open_order = 1
                    self.state_df.loc[0,
                                      'long_strategy_short_order_status'] = self.long_strategy_short_open_order

                elif order_type == 'BUY' and self.short_strategy_signal == 'short_exit':
                    self.short_strategy_long_open_order = 1
                    self.state_df.loc[0,
                                      'short_strategy_long_order_status'] = self.short_strategy_long_open_order

                elif order_type == 'SELL' and self.short_strategy_signal == 'short_exit':
                    self.short_strategy_short_open_order = 1
                    self.state_df.loc[0,
                                      'short_strategy_short_order_status'] = self.short_strategy_short_open_order

                self.state_df.to_pickle(
                    r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                open_order = 1

            except Exception as e:

                print(f'Error while sending {order_type} order for {trading_symbol} position: ', e)
                logger.error(
                    f'Error while sending {order_type} order for {trading_symbol} position: ', e)
                print()

                bot.send_message(
                    chat_id=chat_id, text=f'Error while sending {order_type} order for {trading_symbol} position: {e}', disable_web_page_preview=True, disable_notification=True)

                self.error = 1
                self.pit_stop()
                break

            if open_order == 1:

                print(f'{order_type} order for {trading_symbol} with {order_id} sent successfully')

                bot.send_message(chat_id=chat_id, text=f'{order_type} order for {trading_symbol} with {order_id} sent successfully',
                                 disable_web_page_preview=True, disable_notification=True)

                limit_order_wait_count = 0
                while True:

                    try:
                        time.sleep(5)
                        order_status = self.obj_oms.get_order_history(order_id)['status'].iloc[-1]

                    except Exception as e:

                        print(f'Error while getting order status for order id {order_id}: ', e)
                        logger.error(
                            f'Error while getting order status for order id {order_id}: ', e)
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'Error while getting order status for order id {order_id}: {e}', disable_web_page_preview=True, disable_notification=True)

                        self.error = 1
                        self.pit_stop()
                        break

                    if order_status == 'COMPLETE':

                        market_order_complete = 1

                        if order_type == 'BUY' and self.long_strategy_signal == 'long_exit':
                            self.long_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                            self.long_strategy_short_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_position_status'] = self.long_strategy_short_position
                            self.state_df.loc[0, 'long_strategy_short_option_symbol'] = ''
                            self.state_df.loc[0, 'long_strategy_order_id_short_option'] = ''

                        elif order_type == 'SELL' and self.long_strategy_signal == 'long_exit':

                            self.long_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                            self.long_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_position_status'] = self.long_strategy_long_position
                            self.state_df.loc[0, 'long_strategy_long_option_symbol'] = ''
                            self.state_df.loc[0, 'long_strategy_order_id_long_option'] = ''

                        elif order_type == 'BUY' and self.short_strategy_signal == 'short_exit':
                            self.short_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                            self.short_strategy_short_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_position_status'] = self.short_strategy_short_position
                            self.state_df.loc[0, 'short_strategy_short_option_symbol'] = ''
                            self.state_df.loc[0, 'short_strategy_order_id_short_option'] = ''

                        elif order_type == 'SELL' and self.short_strategy_signal == 'short_exit':

                            self.short_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                            self.short_strategy_long_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_position_status'] = self.short_strategy_long_position
                            self.state_df.loc[0, 'short_strategy_long_option_symbol'] = ''
                            self.state_df.loc[0, 'short_strategy_order_id_long_option'] = ''

                        print(f'{order_type} order for {trading_symbol} with {order_id} complete')
                        logger.info(
                            f'{order_type} order for {trading_symbol} with {order_id} complete')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'{order_type} order for {trading_symbol} with {order_id} complete', disable_web_page_preview=True, disable_notification=True)

                        print(f'Getting {order_type} position after order execution complete')
                        print()

                        bot.send_message(
                            chat_id=chat_id, text=f'Getting {order_type} position after order execution complete', disable_web_page_preview=True, disable_notification=True)

                        try:

                            current_position = self.obj_oms.get_positions_net()
                            self.trade_log_df = self.trade_log_df.append(
                                current_position[current_position['tradingsymbol'] == trading_symbol])

                        except Exception as e:

                            print(f'Error while getting {trading_symbol} position: ', e)
                            logger.error(f'Error while getting {trading_symbol} position: ', e)
                            print()

                            bot.send_message(
                                chat_id=chat_id, text=f'Error while getting {trading_symbol} position: {e}', disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()
                            break

                        self.state_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

                        self.trade_log_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')
                        break

                    elif order_status == 'REJECTED':

                        if order_type == 'BUY' and self.long_strategy_signal == 'long_exit':
                            self.long_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                            self.long_strategy_short_position = 1
                            self.state_df.loc[0,
                                              'long_strategy_short_position_status'] = self.long_strategy_short_position

                        elif order_type == 'SELL' and self.long_strategy_signal == 'long_exit':

                            self.long_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                            self.long_strategy_long_position = 1
                            self.state_df.loc[0,
                                              'long_strategy_long_position_status'] = self.long_strategy_long_position

                        elif order_type == 'BUY' and self.short_strategy_signal == 'short_exit':
                            self.short_strategy_long_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                            self.short_strategy_short_position = 1
                            self.state_df.loc[0,
                                              'short_strategy_short_position_status'] = self.short_strategy_short_position

                        elif order_type == 'SELL' and self.short_strategy_signal == 'short_exit':

                            self.short_strategy_short_open_order = 0
                            self.state_df.loc[0,
                                              'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                            self.short_strategy_long_position = 1
                            self.state_df.loc[0,
                                              'short_strategy_long_position_status'] = self.short_strategy_long_position

                        self.error = 1
                        limit_order_complete = 1
                        print(f'{order_type} order for {trading_symbol} rejected')

                        bot.send_message(
                            chat_id=chat_id, text=f'{order_type} order for {trading_symbol} rejected', disable_web_page_preview=True, disable_notification=True)

                        logger.critical(f'{order_type} order for {trading_symbol} rejected')
                        print()
                        print('Exit the program')
                        print()

                        bot.send_message(chat_id=chat_id, text='Exit the program',
                                         disable_web_page_preview=True, disable_notification=True)

                        self.state_df.to_pickle(
                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                        break

                    else:

                        try:

                            order_received_time = self.obj_oms.get_order_history(
                                order_id)['order_timestamp'].iloc[0].time()

                        except Exception as e:

                            print(
                                f'Error for order_received_time for {trading_symbol} position: ', e)
                            logger.error(
                                f'Error for order_received_time for {trading_symbol} position: ', e)
                            print()

                            bot.send_message(
                                chat_id=chat_id, text=f'Error for order_received_time for {trading_symbol} position: {e}', disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()
                            break

                        if (datime.datetime.now().time() - order_received_time).seconds == 60:
                            print(f'{order_type} order still pending. Order status is: ', order_status)
                            logger.error(
                                f'{order_type} order still pending. Order status is: ', order_status)

                            bot.send_message(
                                chat_id=chat_id, text=f'{order_type} order still pending. Order status is: {order_status}', disable_web_page_preview=True, disable_notification=True)

                        if (datime.datetime.now().time() - order_received_time).seconds >= 120:

                            print('Order still pending. Order status is: ', order_status)
                            logger.critical(
                                'Order still pending after 120 seconds. Order status is: ', order_status)
                            print()

                            bot.send_message(
                                chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                            print('Exit the program')
                            print()

                            bot.send_message(chat_id=chat_id, text='Exit the program',
                                             disable_web_page_preview=True, disable_notification=True)

                            if order_type == 'BUY' and self.long_strategy_signal == 'long_exit':
                                self.long_strategy_short_position = 1
                                self.long_strategy_long_open_order = 1
                                self.state_df.loc[0,
                                                  'long_strategy_long_order_status'] = self.long_strategy_long_open_order
                                self.state_df.loc[0,
                                                  'long_strategy_short_position_status'] = self.long_strategy_short_position

                            elif order_type == 'SELL' and self.long_strategy_signal == 'long_exit':

                                self.long_strategy_long_position = 1
                                self.long_strategy_short_open_order = 1
                                self.state_df.loc[0,
                                                  'long_strategy_short_order_status'] = self.long_strategy_short_open_order
                                self.state_df.loc[0,
                                                  'long_strategy_long_position_status'] = self.long_strategy_long_position

                            elif order_type == 'BUY' and self.short_strategy_signal == 'short_exit':

                                self.short_strategy_short_position = 1
                                self.short_strategy_long_open_order = 1
                                self.state_df.loc[0,
                                                  'short_strategy_long_order_status'] = self.short_strategy_long_open_order
                                self.state_df.loc[0,
                                                  'short_strategy_short_position_status'] = self.short_strategy_short_position

                            elif order_type == 'SELL' and self.short_strategy_signal == 'short_exit':

                                self.short_strategy_long_position = 1
                                self.short_strategy_short_open_order = 1
                                self.state_df.loc[0,
                                                  'short_strategy_short_order_status'] = self.short_strategy_short_open_order
                                self.state_df.loc[0,
                                                  'short_strategy_long_position_status'] = self.short_strategy_long_position

                            limit_order_complete = 1
                            self.error = 1
                            self.state_df.to_pickle(
                                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                            break

    def pit_stop(self):

        print('Entered pit stop!')
        print('Current status as follows...')
        print()
        print('long_strategy_signal_status: ', self.long_strategy_signal)
        print()
        print('short_strategy_signal_status: ', self.short_strategy_signal)
        print()
        print('long open order of long startegy: ', self.long_strategy_long_open_order)
        print()
        print('short open order of long strategy: ', self.long_strategy_short_open_order)
        print()
        print('long open order of short startegy: ', self.short_strategy_long_open_order)
        print()
        print('short open order of short strategy: ', self.short_strategy_short_open_order)
        print()
        print('long position of long strategy: ', self.long_strategy_long_position)
        print()
        print('short position of long strategy: ', self.long_strategy_short_position)
        print()
        print('long position of short strategy: ', self.short_strategy_long_position)
        print()
        print('short position of short strategy: ', self.short_strategy_short_position)
        print()

        bot.send_message(chat_id=chat_id, text=f'PIT STOP: long_strategy_signal_status: {self.long_strategy_signal}, short_strategy_signal_status: {self.short_strategy_signal},  long open order of long startegy: {self.long_strategy_long_open_order}, short open order of long strategy: {self.long_strategy_short_open_order}, long open order of short startegy: {self.short_strategy_long_open_order}, short open order of short strategy: {self.short_strategy_short_open_order}, long position of long strategy: {self.long_strategy_long_position}, short position of long strategy: {self.long_strategy_short_position}, long position of short strategy: {self.short_strategy_long_position}, short position of short strategy: {self.short_strategy_short_position}, disable_web_page_preview=True, disable_notification=True)

        time_before_check = datetime.datetime.now().time()

        self.state_df.to_pickle(
            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

        self.trade_log_df.to_pickle(
            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')

        while True:

            try:
                self.obj_oms.reset_access_token()
                self.obj_oms.kite.ltp(['NSE:MARUTI'])
                print('connected to internet!')
                self.error = 0
                break

            except:
                if (datetime.datetime.now().time() - time_before_check).seconds % 120 == 0:
                    print('not able to connect to internet!')
                    logger.error('not able to connect to internet!')

                    bot.send_message(chat_id=chat_id, text='not able to connect to internet!',
                                     disable_web_page_preview=True, disable_notification=True)

        self.error = 1

        # to_continue = input('Do you want to continue? (Y/N): ')  # Ask if you want to continue
        # logger.info("Again started after confirmation as Y...")
        #
        # if to_continue == 'Y':
        #     self.error = 0
        #
        # else:
        #     self.error = 1
        #
        # return None

    def execution_engine(self):

        self.error = 0
        # print_count = 0

        internal_logic_test = 0

        signal_check_counter = 0

        while (datetime.datetime.now().time() >= self.start_time) and (datetime.datetime.now().time() <= self.end_time):

            if self.error == 1:

                self.state_df.to_pickle(
                    r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

                self.trade_log_df.to_pickle(
                    r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')

                print('Check error')
                logger.error("error has to be find out...")

                bot.send_message(chat_id=chat_id, text='Check error',
                                 disable_web_page_preview=True, disable_notification=True)

                break

            if ((datetime.datetime.now().time().minute) % 5 != 0):

                signal_check_counter = 0

            if ((datetime.datetime.now().time().minute) % 5 == 0) and signal_check_counter == 0:

                signal_check_counter += 1

                internal_logic_test = 0

                print('Checking signal update')

                bot.send_message(chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent',
                                 disable_web_page_preview=True, disable_notification=True)

                try:
                    self.get_historical_data()
                    self.put_rsi()
                    self.generate_signal()

                except Exception as e:
                    print('Error while getting data & signals: ', e)
                    logger.error('Error while getting data & signals: ', e)
                    self.error = 1
                    print()

                    bot.send_message(
                        chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                    break

                current_position_retry_count = 0

                if self.long_strategy_position == 1 and self.long_strategy_signal == 'long_exit' and self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 0:

                    if self.long_strategy_short_position == 1 and self.long_strategy_long_position == 1:

                        self.place_option_market_order_for_exit(order_type='BUY', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                trading_symbol=self.long_strategy_leg_trading_symbol_short, signal='long_exit')

                    if self.long_strategy_short_position == 0 and self.long_strategy_long_position == 1:

                        self.place_option_market_order_for_exit(order_type='SELL', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                trading_symbol=self.long_strategy_leg_trading_symbol_long, signal='long_exit')

                        if self.long_strategy_long_position == 0:
                            self.long_strategy_position = 0
                            self.state_df.loc[0,
                                              'long_strategy_position'] = self.long_strategy_position
                            self.state_df.to_pickle(
                                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                            logger.info("Wao!!! We exited from long strategy position ...")

                if self.short_strategy_position == 1 and self.short_strategy_signal == 'short_exit' and self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 0:

                    if self.short_strategy_short_position == 1 and self.short_strategy_long_position == 1:

                        self.place_option_market_order_for_exit(order_type='BUY', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                trading_symbol=self.short_strategy_leg_trading_symbol_short, signal='short_exit')

                    if self.short_strategy_short_position == 0 and self.short_strategy_long_position == 1:

                        self.place_option_market_order_for_exit(order_type='SELL', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                trading_symbol=self.short_strategy_leg_trading_symbol_long, signal='short_exit')

                        if self.short_strategy_long_position == 0:
                            self.short_strategy_position = 0
                            self.state_df.loc[0,
                                              'short_strategy_position'] = self.short_strategy_position
                            self.state_df.to_pickle(
                                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                            logger.info("Wao!!! We exited from short strategy position ...")

                if self.long_strategy_position == 0 and self.long_strategy_signal == 'long_entry':

                    if self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 0:

                        if self.long_strategy_long_position == 0:

                            self.get_option_trading_symbols()

                            self.place_option_limit_order_for_entry(order_type='BUY', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                    trading_symbol=self.long_strategy_leg_trading_symbol_long, signal='long_entry')

                        if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 0:

                            self.place_option_limit_order_for_entry(order_type='SELL', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                    trading_symbol=self.long_strategy_leg_trading_symbol_short, signal='long_entry')

                            if self.long_strategy_short_position == 1:
                                self.long_strategy_position = 1
                                self.state_df.loc[0,
                                                  'long_strategy_position'] = self.long_strategy_position
                                self.state_df.to_pickle(
                                    r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                logger.info("Hurrey!!! long strategy position has been placed...")

                if self.short_strategy_position == 0 and self.short_strategy_signal == 'short_entry':

                    if self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 0:

                        if self.short_strategy_long_position == 0:

                            self.get_option_trading_symbols()

                            self.place_option_limit_order_for_entry(order_type='BUY', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                    trading_symbol=self.short_strategy_leg_trading_symbol_long, signal='short_entry')

                        if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 0:

                            self.place_option_limit_order_for_entry(order_type='SELL', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                    trading_symbol=self.short_strategy_leg_trading_symbol_short, signal='short_entry')

                            if self.short_strategy_short_position == 1:
                                self.short_strategy_position = 1
                                self.state_df.loc[0,
                                                  'short_strategy_position'] = self.short_strategy_position
                                self.state_df.to_pickle(
                                    r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                logger.info("Hurrey!!! short strategy position has been placed...")

                else:
                    print('No change...')

                    bot.send_message(chat_id=chat_id, text='No change...',
                                     disable_web_page_preview=True, disable_notification=True)

            else:

                if internal_logic_test == 0:

                    internal_logic_test += 1

                    print('Beginning internal logic test...')

                    bot.send_message(
                        chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                    if self.long_strategy_signal == 'long_entry':

                        if self.long_strategy_long_open_order == 1 and self.long_strategy_short_open_order == 0:

                            if self.long_strategy_position == 0:

                                if self.long_strategy_long_position == 0 and self.long_strategy_short_position == 0:

                                    print(
                                        'long order for entry into long option leg for long entry is open when signal is long entry and both long position and short position is 0')

                                    bot.send_message(chat_id=chat_id, text='long order for entry into long option leg for long entry is open when signal is long entry and both long position and short position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because both long position and short position is not 0 when long open order is 1 and short open order is 0 and signal is long entry and long strategy position is 0')

                                    bot.send_message(chat_id=chat_id, text='Error because both long position and short position is not 0 when long open order is 1 and short open order is 0 and signal is long entry and long strategy position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 1, short open order is 0, long startegy position is 1 and signal is long entry')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 1, short open order is 0, long startegy position is 1 and signal is long entry',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 1:

                            if self.long_strategy_position == 0:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 0:

                                    print(
                                        'long order for entry into long option leg for long entry is complete and short open order is 1 and signal is long entry and long position is 1 and short position is 0')

                                    bot.send_message(chat_id=chat_id, text='long order for entry into long option leg for long entry is complete and short open order is 1 and signal is long entry and long position is 1 and short position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because both long position and short position is not 1 and 0 when long open order is 0, short open order is 1 and long strategy position is 0 and siganl is long entry')

                                    bot.send_message(chat_id=chat_id, text='Error because both long position and short position is not 1 and 0 when long open order is 0, short open order is 1 and long strategy position is 0 and siganl is long entry',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:
                                print(
                                    'Error because long open order is 0, short open order is 1, long startegy position is 1 and signal is long entry')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 0, short open order is 1, long startegy position is 1 and signal is long entry',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.long_strategy_long_open_order == 1 and self.long_strategy_short_open_order == 1:

                            print(
                                'Error because both long open order and short open order is 1 and signal is long entry')

                            bot.send_message(chat_id=chat_id, text='Error because both long open order and short open order is 1 and signal is long entry',
                                             disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()

                        elif self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 0:

                            if self.long_strategy_position == 0:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 0:

                                    self.place_option_limit_order_for_entry(order_type='SELL', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                            trading_symbol=self.long_strategy_leg_trading_symbol_short, signal='long_entry')

                                    if self.long_strategy_short_position == 1:
                                        self.long_strategy_position = 1
                                        self.state_df.loc[0,
                                                          'long_strategy_position'] = self.long_strategy_position
                                        self.state_df.to_pickle(
                                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                        logger.info(
                                            "Hurrey!!! long strategy position has been placed...")

                                elif self.long_strategy_long_position == 0 and self.long_strategy_short_position == 0:

                                    print(
                                        'Error because signal is long entry both open orders are 0 and no open positions. This case should not exist because when signal becomes long entry we should immediately get into position.')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is long entry both open orders are 0 and no open positions. This case should not exist because when signal becomes long entry we should immediately get into position.',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because signal is long entry, long open order and short open order are 0 and either both positions are 1 or only short position is 1. This should not exist')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is long entry, long open order and short open order are 0 and either both positions are 1 or only short position is 1. This should not exist',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 1:

                                    print('We are in long position!')

                                    bot.send_message(
                                        chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because signal is long entry and long strategy position is 1 and both positions are not 1')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is long entry and long strategy position is 1 and both positions are not 1',
                                                     disable_web_page_preview=True, disable_notification=True)

                    elif self.long_strategy_signal == 'long_exit':

                        if self.long_strategy_long_open_order == 1 and self.long_strategy_short_open_order == 0:

                            if self.long_strategy_position == 1:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 1:

                                    print(
                                        'long order for exit out of short option leg is open, long and short position is 1, long strategy position is 1 and signal is long exit')

                                    bot.send_message(chat_id=chat_id, text='long order for exit out of short option leg is open, long and short position is 1, long strategy position is 1 and signal is long exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print(
                                        'Complete the exit order for the short position and exit the long position')

                                    bot.send_message(chat_id=chat_id, text='Complete the exit order for the short position and exit the long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because long open order for short position exit is 1, short open order is 0, long strategy position is 1 and signal is long exit but long position and short position both are not 1')

                                    bot.send_message(chat_id=chat_id, text='Error because long open order for short position exit is 1, short open order is 0, long strategy position is 1 and signal is long exit but long position and short position both are not 1',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 1, short open order is 0, long startegy position is 0 and signal is long exit')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 1, short open order is 0, long startegy position is 0 and signal is long exit',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 1:

                            if self.long_strategy_position == 1:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 0:

                                    print(
                                        'short order for exit out of long position is 1, long order is 0, short position is 0, long position is 1, long strategy position is 1 and signal is long exit')

                                    bot.send_message(chat_id=chat_id, text='short order for exit out of long position is 1, long order is 0, short position is 0, long position is 1, long strategy position is 1 and signal is long exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print('Complete exit order for long position')

                                    bot.send_message(chat_id=chat_id, text='Complete exit order for long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because short open order is 1, long open order is 0, long strategy position is 1, long position and short position is not 1 and 0 when signal is long exit')

                                    bot.send_message(chat_id=chat_id, text='Error because short open order is 1, long open order is 0, long strategy position is 1, long position and short position is not 1 and 0 when signal is long exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 0, short open order is 1, long strategy position is 0 when signal is long exit')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 0, short open order is 1, long strategy position is 0 when signal is long exit',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.long_strategy_long_open_order == 1 and self.long_strategy_short_open_order == 1:

                            print(
                                'Error because both long open order and short open order is 1 and signal is long exit')

                            bot.send_message(chat_id=chat_id, text='Error because both long open order and short open order is 1 and signal is long exit',
                                             disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()

                        elif self.long_strategy_long_open_order == 0 and self.long_strategy_short_open_order == 0:

                            if self.long_strategy_position == 0:

                                if self.long_strategy_long_position == 0 and self.long_strategy_short_position == 0:

                                    print(
                                        'No position on as signal is long exit, open orders are 0,long strategy position is 0 and both long and short position is 0 when signal is long exit')

                                    bot.send_message(chat_id=chat_id, text='No position on as signal is long exit, open orders are 0,long strategy position is 0 and both long and short position is 0 when signal is long exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because long position and short position are both not 0, long strategy position is 0 when signal is long exit and there are no open orders')

                                    bot.send_message(chat_id=chat_id, text='Error because long position and short position are both not 0, long strategy position is 0 when signal is long exit and there are no open orders',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                if self.long_strategy_long_position == 1 and self.long_strategy_short_position == 0:

                                    print(
                                        'Exited from short position, still in long position and no orders are open when signal is long exit')

                                    bot.send_message(chat_id=chat_id, text='Exited from short position, still in long position and no orders are open when signal is long exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print('Sending exit order for long position')

                                    bot.send_message(chat_id=chat_id, text='Sending exit order for long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.place_option_market_order_for_exit(order_type='SELL', exchange_symbol=self.long_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                            trading_symbol=self.long_strategy_leg_trading_symbol_long, signal='long_exit')

                                    if self.long_strategy_long_position == 0:
                                        self.long_strategy_position = 0
                                        self.state_df.loc[0,
                                                          'long_strategy_position'] = self.long_strategy_position
                                        self.state_df.to_pickle(
                                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                        logger.info(
                                            "Hurrey!!! long strategy position has been placed...")

                                else:

                                    print('Error because long position and short position are both not 1 and 0 respectively, long strategy position is 1 when signal is long exit and there are no open orders. Any other scenario should not exist.')

                                    bot.send_message(chat_id=chat_id, text='Error because long position and short position are both not 1 and 0 respectively, long strategy position is 1 when signal is long exit and there are no open orders. Any other scenario should not exist.',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                    # for short streetegy:

                    if self.short_strategy_signal == 'short_entry':

                        if self.short_strategy_long_open_order == 1 and self.short_strategy_short_open_order == 0:

                            if self.short_strategy_position == 0:

                                if self.short_strategy_long_position == 0 and self.short_strategy_short_position == 0:

                                    print(
                                        'long order for entry into long option leg for short entry is open when signal is short entry and both long position and short position is 0')

                                    bot.send_message(chat_id=chat_id, text='long order for entry into long option leg for short entry is open when signal is short entry and both long position and short position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because both long position and short position is not 0 when long open order is 1 and short open order is 0 and signal is short entry and short strategy position is 0')

                                    bot.send_message(chat_id=chat_id, text='Error because both long position and short position is not 0 when long open order is 1 and short open order is 0 and signal is short entry and short strategy position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 1, short open order is 0, short startegy position is 1 and signal is short entry')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 1, short open order is 0, short startegy position is 1 and signal is short entry',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 1:

                            if self.short_strategy_position == 0:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 0:

                                    print(
                                        'long order for entry into long option leg for short entry is complete and short open order is 1 and signal is short entry and long position is 1 and short position is 0')

                                    bot.send_message(chat_id=chat_id, text='long order for entry into long option leg for short entry is complete and short open order is 1 and signal is short entry and long position is 1 and short position is 0',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because both long position and short position is not 1 and 0 when long open order is 0, short open order is 1 and short strategy position is 0 and siganl is short entry')

                                    bot.send_message(chat_id=chat_id, text='Error because both long position and short position is not 1 and 0 when long open order is 0, short open order is 1 and short strategy position is 0 and siganl is short entry',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:
                                print(
                                    'Error because long open order is 0, short open order is 1, short startegy position is 1 and signal is short entry')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 0, short open order is 1, short startegy position is 1 and signal is short entry',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.short_strategy_long_open_order == 1 and self.short_strategy_short_open_order == 1:

                            print(
                                'Error because both long open order and short open order is 1 and signal is short entry')

                            bot.send_message(chat_id=chat_id, text='Error because both long open order and short open order is 1 and signal is short entry',
                                             disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()

                        elif self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 0:

                            if self.short_strategy_position == 0:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 0:

                                    self.place_option_limit_order_for_entry(order_type='SELL', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_short,
                                                                            trading_symbol=self.short_strategy_leg_trading_symbol_short, signal='short_entry')

                                    if self.short_strategy_short_position == 1:
                                        self.short_strategy_position = 1
                                        self.state_df.loc[0,
                                                          'short_strategy_position'] = self.short_strategy_position
                                        self.state_df.to_pickle(
                                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                        logger.info(
                                            "Hurrey!!! long strategy position has been placed...")

                                elif self.short_strategy_long_position == 0 and self.short_strategy_short_position == 0:

                                    print(
                                        'Error because signal is short entry both open orders are 0 and no open positions. This case should not exist because when signal becomes short entry we should immediately get into position.')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is short entry both open orders are 0 and no open positions. This case should not exist because when signal becomes short entry we should immediately get into position.',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because signal is short entry, long open order and short open order are 0 and either both positions are 1 or only short position is 1. This should not exist')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is short entry, long open order and short open order are 0 and either both positions are 1 or only short position is 1. This should not exist',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 1:

                                    print('We are in short position!')

                                    bot.send_message(chat_id=chat_id, text='We are in short position!',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because signal is short entry and short strategy position is 1 and both positions are not 1')

                                    bot.send_message(chat_id=chat_id, text='Error because signal is short entry and short strategy position is 1 and both positions are not 1',
                                                     disable_web_page_preview=True, disable_notification=True)

                    elif self.short_strategy_signal == 'short_exit':

                        if self.short_strategy_long_open_order == 1 and self.short_strategy_short_open_order == 0:

                            if self.short_strategy_position == 1:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 1:

                                    print(
                                        'long order for exit out of short option leg is open, long and short position is 1, short strategy position is 1 and signal is short exit')

                                    bot.send_message(chat_id=chat_id, text='long order for exit out of short option leg is open, long and short position is 1, short strategy position is 1 and signal is short exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print(
                                        'Complete the exit order for the short position and exit the long position')

                                    bot.send_message(chat_id=chat_id, text='Complete the exit order for the short position and exit the long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because long open order for short position exit is 1, short open order is 0, short strategy position is 1 and signal is short exit but long position and short position both are not 1')

                                    bot.send_message(chat_id=chat_id, text='Error because long open order for short position exit is 1, short open order is 0, short strategy position is 1 and signal is short exit but long position and short position both are not 1',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 1, short open order is 0, short startegy position is 0 and signal is short exit')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 1, short open order is 0, short startegy position is 0 and signal is short exit',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 1:

                            if self.short_strategy_position == 1:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 0:

                                    print(
                                        'short order for exit out of long position is 1, long order is 0, short position is 0, long position is 1, short strategy position is 1 and signal is short exit')

                                    bot.send_message(chat_id=chat_id, text='short order for exit out of long position is 1, long order is 0, short position is 0, long position is 1, short strategy position is 1 and signal is short exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print('Complete exit order for long position')

                                    bot.send_message(chat_id=chat_id, text='Complete exit order for long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because short open order is 1, long open order is 0, short strategy position is 1, long position and short position is not 1 and 0 when signal is short exit')

                                    bot.send_message(chat_id=chat_id, text='Error because short open order is 1, long open order is 0, short strategy position is 1, long position and short position is not 1 and 0 when signal is short exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                print(
                                    'Error because long open order is 0, short open order is 1, short strategy position is 0 when signal is short exit')

                                bot.send_message(chat_id=chat_id, text='Error because long open order is 0, short open order is 1, short strategy position is 0 when signal is short exit',
                                                 disable_web_page_preview=True, disable_notification=True)

                                self.error = 1
                                self.pit_stop()

                        elif self.short_strategy_long_open_order == 1 and self.short_strategy_short_open_order == 1:

                            print(
                                'Error because both long open order and short open order is 1 and signal is short exit')

                            bot.send_message(chat_id=chat_id, text='Error because both long open order and short open order is 1 and signal is short exit',
                                             disable_web_page_preview=True, disable_notification=True)

                            self.error = 1
                            self.pit_stop()

                        elif self.short_strategy_long_open_order == 0 and self.short_strategy_short_open_order == 0:

                            if self.short_strategy_position == 0:

                                if self.short_strategy_long_position == 0 and self.short_strategy_short_position == 0:

                                    print(
                                        'No position on as signal is short exit, open orders are 0, short strategy position is 0 and both long and short position is 0')

                                    bot.send_message(
                                        chat_id=chat_id, text=f'{order_type} limit order for leg {trading_symbol} with order id {order_id} has been sent', disable_web_page_preview=True, disable_notification=True)

                                else:

                                    print(
                                        'Error because long position and short position are both not 0, short strategy position is 0 when signal is short exit and there are no open orders')

                                    bot.send_message(chat_id=chat_id, text='Error because long position and short position are both not 0, short strategy position is 0 when signal is short exit and there are no open orders',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

                            else:

                                if self.short_strategy_long_position == 1 and self.short_strategy_short_position == 0:

                                    print(
                                        'Exited from short position, still in long position and no orders are open when signal is short exit')

                                    bot.send_message(chat_id=chat_id, text='Exited from short position, still in long position and no orders are open when signal is short exit',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    print('Sending exit order for long position')

                                    bot.send_message(chat_id=chat_id, text='Sending exit order for long position',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.place_option_market_order_for_exit(order_type='SELL', exchange_symbol=self.short_strategy_leg_option_trading_symbol_with_exchange_long,
                                                                            trading_symbol=self.short_strategy_leg_trading_symbol_long, signal='long_exit')

                                    if self.short_strategy_long_position == 0:
                                        self.short_strategy_position = 0
                                        self.state_df.loc[0,
                                                          'short_strategy_position'] = self.short_strategy_position
                                        self.state_df.to_pickle(
                                            r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')
                                        logger.info(
                                            "Hurrey!!! long strategy position has been placed...")

                                else:

                                    print('Error because long position and short position are both not 1 and 0 respectively, short strategy position is 1 when signal is short exit and there are no open orders. Any other scenario should not exist.')

                                    bot.send_message(chat_id=chat_id, text='Error because long position and short position are both not 1 and 0 respectively, short strategy position is 1 when signal is short exit and there are no open orders. Any other scenario should not exist.',
                                                     disable_web_page_preview=True, disable_notification=True)

                                    self.error = 1
                                    self.pit_stop()

        if (datetime.datetime.now().time() >= self.end_time):

            self.state_df.to_pickle(
                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_STATE_DF_TEST-01.pkl')

            self.trade_log_df.to_pickle(
                r'D:\ALGO TRADING\LIVE PROJECTS\LIVE TRADINGS\OTHER OPTION STRATEGIES\BEAR & BULL PUT SPREAD\BEAR_BULL_TREND FOLLOWING STRATEGY_TRADE_LOG_DF_TEST-01.pkl')


obj_StrategyExecution = StrategyExecution(exchange='NFO', underlying='NIFTY', instrument_type='option', expiry_status='weekly',
                                          segment='NFO-OPT', option_type=None, strike_price=None, lots=1, rsi_fast=5, rsi_slow=14, data_days=3, data_interval='5minute')


start_time = datetime.datetime.now().time()

while datetime.datetime.now().time() < datetime.time(9, 15):

    time.sleep(seconds=(datetime.datetime.now().time() - start_time).seconds - 10)

    obj_StrategyExecution.execution_engine()


obj_StrategyExecution.state_df
