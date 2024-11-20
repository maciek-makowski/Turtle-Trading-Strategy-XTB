import math
import time
import requests
import sys
import json
import base64
import yfinance as yf 
import pandas as pd
import numpy as np 
from connection_login import XTB
from datetime import datetime, timedelta
from app import Signal

PASSWORD = "M_aku17@65"
ID = "17071659"
# ID = "50157835" 
URL = f"https://signals-db-234640427180.europe-central2.run.app"
RISK_PER_BUY = 0.1
TAKE_PROFIT_FACTOR = 3


total_profit = 0
profitable_transactions = 0
transactions = 0
#account_size = 10000
tickers = []
def get_active_signals():
    response = requests.get(URL + "/get_active_signals")
    print("Query get active signals", response.text)
    return response.json()


def get_waiting_for_purchase_signals():
    response = requests.get(URL + "/get_considered_signals")
    # print("Query get waiting for purchase signals", response.text)
    return response.json()

def add_signal_to_db(purchase_signal):
    '''
    purchas_signal: Signal class
    '''
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "MyApp/1.0"
    }
    response = requests.post(URL + "/add_signal", json=purchase_signal.to_dict(), headers=headers)

    # print("Status Code:", response.status_code) 
    # print("Response JSON:", response.json())
    return response.json()


def modify_signal_data(purchase_signal):
    '''
    purchase_signal: Signal class
    '''
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "MyApp/1.0"
    }
    response = requests.post(URL + "/modify_signal", json=purchase_signal.to_dict(), headers=headers)

    # print("Status Code:", response.status_code) 
    # print("Response JSON:", response.json())
    return response.json()

def add_potential_signals_to_db(XTB, positions_to_open):
    for position in positions_to_open:
        purchase_signal = Signal(position)
        symbol = position['ticker'] + ".US_9"
        purchase_signal.most_recent_price = XTB.get_current_price(symbol)
        time.sleep(0.2)
        purchase_signal.status = 2
        add_signal_to_db(purchase_signal)

def check_signal_prices_modify_params(XTB, signals_list):
    for signal_data in signals_list:
        signal = Signal(signal_data)
        symbol = signal.ticker + ".US_9"
        signal.most_recent_price = XTB.get_current_price(symbol)
        time.sleep(0.2)
        if signal.most_recent_price < signal.stop_loss and signal.status == 1:
            signal.status = 3 
        elif signal.risk > RISK_PER_BUY:
            signal.status = 3 
        modify_signal_data(signal)

def calc_donchain(data):
    temp = data.iloc[:-1]
    data['upper'] = temp['High'].rolling(window = 20).max()
    data['lower'] = temp['Low'].rolling(window = 10).min()
    
    return data


def get_nasdaq_tickers(file_loc):
    tickers = pd.read_csv(file_loc)
    return tickers['Ticker'].to_list()

def generate_buy_signal(tickers, start, end, active_signals):
    count = 0
    buy_singals_list = []
    active_signals = list(active_signals)
    for index, x in enumerate(active_signals): 
        active_signals[index] = x.replace(".US_9","")
        
    print("Active signals",active_signals)
    for symbol in tickers: 

        if symbol in active_signals:
            continue 

        ticker = yf.Ticker(str(symbol))
        history = ticker.history(interval='1d', start= start, end= end)
        
        if history.empty:
            print("smth went wrong")
            continue

        history = history.iloc[:-1]

        history = history.reset_index()
        history = calc_donchain(history)
        length = len(history['Close']) - 1

        todays_close = history['Close'].iloc[length]
        donchain_close = history['upper'].iloc[length-1]
        stop_loss = history['lower'].iloc[length-1]
        risk = (todays_close - stop_loss)/todays_close

        #print(history)

        if todays_close > donchain_close and risk < RISK_PER_BUY :
            #print("Buy has been generated")
            buy_signal = {}
            buy_signal['ticker'] = symbol
            buy_signal['generation_price'] = todays_close
            buy_signal['stop_loss'] = stop_loss
            buy_signal['take_profit'] = todays_close + TAKE_PROFIT_FACTOR*(todays_close - stop_loss)
            buy_signal['date_of_gen'] = history['Date'].iloc[length].isoformat()
            #buy_signal['no_stocks'] = math.ceil(POSITION_SIZE/todays_close)
            buy_signal['risk'] = risk
            max_risk = 200
            no_stocks = math.floor(max_risk/(risk*todays_close)) 
            buy_signal['no_stocks'] = no_stocks
            #buy_signal['no_stocks'] = API.calc_position_size(risk, todays_close)

            buy_singals_list.append(buy_signal)
            
            count = count + 1


            #print("Difference", todays_close - donchain_close)
            #print(buy_singal)
            
            
    return count, buy_singals_list

def calc_trailing_SL(last_SL, last_price, opening_price):
    SL = last_SL
    print("last price", last_price)
    print("last sl", last_SL)
    if last_price > 1.025 * opening_price:
        if last_SL < opening_price:
            SL = 1.001 * opening_price

            return SL 

        growth = (last_price / opening_price) - 1

        increment = math.floor((growth / 0.025) - 1) 
        new_SL = opening_price + (0.025 * increment * opening_price)

        if new_SL > last_SL:
            SL = new_SL

    return SL             
   
def track_profit(tickers, start_day, end_day, active):
    profit_per_position = {}
    global total_profit, transactions, profitable_transactions


    no_buy_singals, open_positions = generate_buy_signal(tickers, start_day, end_day, active)
    print("Day", end_day, "No_buy_singals", no_buy_singals)
    print("Active signals", active)

    for position in open_positions:
        
        active.append(position['ticker'])

        print("Position", position)


        ticker = yf.Ticker(str(position['ticker']))
        opening_stop_loss = position['stop_loss']
        old_end_day = end_day
        end_day = end_day + timedelta(240)

        position_history = ticker.history(interval='1d', start= old_end_day, end= end_day)

        if position_history.empty:
            continue

        for index, close_price in enumerate(position_history['Close']):
            #position_history['Low'].iloc[index]
            if  position_history['Low'].iloc[index] < position['stop_loss']:
                profit_per_position[position['ticker']] = (position['stop_loss'] - position['opening_price']) * position['no_stocks']
                print("Closed with SL")
                break
            elif close_price > position['take_profit']:
                profit_per_position[position['ticker']] = (position['take_profit'] - position['opening_price']) * position['no_stocks']
                print("Closed with TP")
                break
            else: 
                profit_per_position[position['ticker']] = (close_price - position['opening_price']) * position['no_stocks']
                #position['stop_loss'] = calc_trailing_SL(position_history['Close'].iloc[0:index], position['opening_price'], opening_stop_loss)
                position['stop_loss'] = calc_SL_new3(position['stop_loss'], position_history['Close'].iloc[index], position['opening_price'])

        if profit_per_position[position['ticker']] > 0:
            profitable_transactions = profitable_transactions + 1
        
        transactions = transactions + 1

    print("Profit per position",profit_per_position)

    for ticker in profit_per_position: 
        total_profit = total_profit + profit_per_position[ticker]

    print("Total profit", total_profit)
    if transactions != 0: print("Efficiency", profitable_transactions/transactions)
    print("Total transactions", transactions)

    return active


def hello_pubsub(event, context):
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print("PB mes ", pubsub_message)

    tickers = get_nasdaq_tickers()


    API = XTB(ID, PASSWORD)

    active_signals = []
    trades = API.get_trades()

    for i in trades: 
        active_signals.append(i['symbol'])

    unique_symbols = set(active_signals)
    for symbol in unique_symbols:
        time.sleep(0.2)
        API.check_take_profit(symbol, trades, calc_SL_new3)

    today = datetime.now()
    start_day = today - timedelta(40)
    no_buy_singals, open_positions = generate_buy_signal(tickers, start_day, today, unique_symbols)

    print("Day", today, "No_buy_singals", no_buy_singals)


    for position in open_positions:
        print(position)
        symbol = position['ticker'] + ".US_9"

        
        time.sleep(0.2)
        total_capital, free_funds = API.get_balance()
        print("Total capital", total_capital, "Free funds", free_funds)
        volume = API.calc_position_size(position['risk'], position['opening_price'], total_capital, free_funds)
        if volume == 0:
            print("Volume for the position is 0" )
        if volume > 0 :   
            API.open_pkc(symbol, volume, comment=str(round(position['take_profit'],2)))
            print("Opening position", position, "With volume", volume)
            time.sleep(5)
            print("What can be wrong with the rounded stop loss",  round(position['stop_loss'],2))
            API.set_stop_loss(symbol, volume, round(position['stop_loss'],2))

    API.logout()


def main():
    tickers = get_nasdaq_tickers("./ticker_lists/us100_tickers.csv")

    API = XTB(ID, PASSWORD)

    active_signals = []
    trades = API.get_trades()

    active_signals_to_db = get_active_signals()
    check_signal_prices_modify_params(API, active_signals_to_db['signals'])
   
    print("Trades", trades)
   
    for i in trades: 
        active_signals.append(i['symbol'])

    unique_symbols = set(active_signals)
    for symbol in unique_symbols:
        time.sleep(0.2)
        res = API.check_take_profit(symbol, trades, calc_trailing_SL)
        if res == 'position closed':
            for signal in active_signals_to_db['signals']:
                tick = symbol - "US_9"
                if tick == signal.ticker:
                    signal.status = 3 
                    signal.date_of_expiry = datetime.now().isoformat()
                    modify_signal_data(signal)



    today = datetime.now()
    start_day = today - timedelta(40)
    no_buy_singals, open_positions = generate_buy_signal(tickers, start_day, today, unique_symbols)

    print("Day", today, "No_buy_singals", no_buy_singals)

    add_potential_signals_to_db(API, open_positions)

    waiting_for_purchase = get_waiting_for_purchase_signals()

    check_signal_prices_modify_params(API, waiting_for_purchase['signals'])

    possible_purchases = get_waiting_for_purchase_signals()
    for purchase_data in possible_purchases['signals']:
        purchase = Signal(purchase_data)
        symbol = purchase.ticker + ".US_9"
        total_capital, free_funds = API.get_balance()
        time.sleep(0.2)
        print("Total capital", total_capital, "Free funds", free_funds)
        volume = API.calc_position_size(purchase.risk, purchase.most_recent_price, total_capital, free_funds)
        if volume == 0:
            print(f"Volume for the signal {purchase.ticker} is 0" )

        elif volume > 0 :
            succeded = API.open_pkc(symbol, volume, comment=str(round(purchase.take_profit,2)))
            # print("Opening position", purchase.to_dict(), "With volume", volume)
            print("SUCCEDED", succeded)
            if succeded == True:
                print("Transaction succesful")
                purchase.opening_price = API.get_current_price(symbol)
                time.sleep(0.2)
                purchase.status = 1
                purchase.date_of_purchase = datetime.now().isoformat()
                modify_signal_data(purchase)
            
            time.sleep(5)
            API.set_stop_loss(symbol, volume, round(purchase.stop_loss,2))


    API.logout()


if __name__ == "__main__":
    main()
# if __name__ == "__main__":
#     hello_pubsub('data','context')


