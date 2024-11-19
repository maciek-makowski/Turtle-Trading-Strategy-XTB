import websocket, json 
import math
from datetime import datetime, timedelta

class XTB: 
    def __init__(self, ID, PASSWORD):
        self.ID = ID
        self.PASSWORD = PASSWORD
        self.ws = 0
        self.exec_start = self.get_time()
        self.connect()
        #self.login()
        self.SessionID = self.login()


    def login(self):
        login = {
            "command": "login",
            "arguments": {
                    "userId": self.ID,
                    "password": self.PASSWORD
            }
        }

        login_json = json.dumps(login)
        result = self.send(login_json)
        result = json.loads(result)
        status = result['status']

        if str(status) == "True":
            #success
            return result['streamSessionId']
        else:
            #error
            return False

    def logout(self):
        logout = {
            "command": "logout"
        }

        logout_json = json.dumps(logout)
        result = self.send(logout_json)
        result = json.loads(result)

        status = result["status"]
        self.disconnect()
        

        if str(status) == "True":
                #success
                return True
        else:
                #error
                return False


    ### WEB SOCKETS ####
    def connect(self):
        try:
            #self.ws = websocket.create_connection("wss://ws.xtb.com/demo")
            self.ws = websocket.create_connection("wss://ws.xtb.com/real")
            print("WebSocket connection successful.")
            print(f"WebSocket object: {self.ws}")
            print(f"WebSocket status: {self.ws.status}")
            print(f"WebSocket sock: {self.ws.sock}")
            #success
            return True 
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            #error
            return False

    def disconnect(self):
        try:
            self.ws.close()
            #success
            return True
        except:
            #error
            return False

    def send(self, message):
        self.ws.send(message)
        result = self.ws.recv()
        
        return result + "\n"
    
    def get_all_symbols(self):
        tickers = {
	        "command": "getAllSymbols"
        }
        tickers = json.dumps(tickers)
        result = json.loads(self.send(tickers))

        return result
    
    def get_tickers(self, list_of_tickers): 
        result = []
        for i in list_of_tickers:
            tickers = {
                    "command": "getSymbol",
                    "arguments": {
                        "symbol": f"{i}"
                    }
            }
            tickers = json.dumps(tickers)
            res = json.loads(self.send(tickers))
            result.append(res)
            print(res)


        return result

         

    ### Time operations #################

    def get_time(self):
            time = datetime.today().strftime('%m/%d/%Y %H:%M:%S%f')
            time = datetime.strptime(time, '%m/%d/%Y %H:%M:%S%f')
            return time

    def miliseconds_conversion(self, date):
        start = datetime(1970,1,1,0,0,0)
        duration = date - start
        duration = 1000 * duration.total_seconds()
        return duration

    ### Price action operations ###########

    def get_candles(self, ticker, period, start):
        # PERIOD_M1	  1	            1 minute
        # PERIOD_M5	  5	            5 minutes
        # PERIOD_M15  15	        15 minutes
        # PERIOD_M30  30	        30 minutes
        # PERIOD_H1	  60	        60 minutes (1 hour)
        # PERIOD_H4	  240	        240 minutes (4 hours)
        # PERIOD_D1	  1440	        1440 minutes (1 day)
        # PERIOD_W1	  10080	        10080 minutes (1 week)
        # PERIOD_MN1  43200	        43200 minutes (30 days)
        
        end = self.get_time()
        end = self.miliseconds_conversion(end)
        start = self.miliseconds_conversion(start)

        CHART_RANGE_INFO_RECORD = {
            "end": end,
	        "period": period,
	        "start": start,
	        "symbol": ticker
            # ticks optional returns number of candles if you ever need that
        }
     
        candles = {
	        "command": "getChartRangeRequest",
	        "arguments": {
		        "info": CHART_RANGE_INFO_RECORD
             }
        }
        candles_json = json.dumps(candles)
        result = self.send(candles_json)
        result = json.loads(result)

        date, open, close, high, low = [], [], [], [], []

        #print(result)

        for x in result['returnData']['rateInfos']:
            date.append(x['ctmString'])
            open.append(x['open'])
            close.append(x['close'])
            high.append(x['high'])
            low.append(x['low'])

        return zip(date,open,close,high,low)
    
    ### Placing and getting orders #########

    # Transaction type        CMD         Meaning
    #         0                0          - Buy asking price
    #         0                4          - Buy when reaches the upper limit
    #         0                2          - Buy when reaches the lower limit
    #         0                5          - Set stop loss 
    #         0                3          - Set take profit
    #         0                1          - Close the order (order = 0) delete TP and SL first
    #         4                5          - Delete SL needs the order number
    #         4                3          - Delete TP needs the order number 
    #         3                5          - Modify SL needs the order number
    def open_pkc(self, ticker, volume, comment = ""):
        TRADE_TRANS_INFO = {
            "cmd": 0,
            "customComment": comment,
            "expiration": 0,
            "offset": -1,
            "order": 0,
            "price": 1,
            "symbol": ticker,
            "type": 0,
            "volume": volume
        }
        message = {
	        "command": "tradeTransaction",
	        "arguments": {
		    "tradeTransInfo": TRADE_TRANS_INFO
	        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        return result
    
    def close_pkc(self, order, ticker, sl_order, volume, comment = ""):
        self.delete_stop_loss(ticker, sl_order)
        TRADE_TRANS_INFO = {
            "cmd": 1,
            "customComment": comment,
            "expiration": 0,
            "offset": -1,
            "order": 0,
            "price": 1,
            "symbol": ticker,
            "type": 0,
            "volume": volume
        }
        message = {
	        "command": "tradeTransaction",
	        "arguments": {
		    "tradeTransInfo": TRADE_TRANS_INFO
	        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        return result
        
    def set_stop_loss(self, ticker, volume, price, comment = ""):
        TRADE_TRANS_INFO = {
            "cmd": 5,
            "customComment": comment,
            "expiration": 0,
            "offset": -1,
            "order": 0,
            "price": price,
            "symbol": ticker,
            "type": 0,
            "volume": volume
        }
        message = {
	        "command": "tradeTransaction",
	        "arguments": {
		    "tradeTransInfo": TRADE_TRANS_INFO
	        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        print("Message received after SL set : ", result)

        return result
    
    def delete_stop_loss(self, ticker, order, comment = ""):
        TRADE_TRANS_INFO = {
            "cmd": 5,
            "customComment": comment,
            "expiration": 0,
            "offset": -1,
            "order": order,
            "price": 0,
            "symbol": ticker,
            "type": 4,
            "volume": 0
        }
        message = {
	        "command": "tradeTransaction",
	        "arguments": {
		    "tradeTransInfo": TRADE_TRANS_INFO
	        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        print("Message received after SL deletion : ", result)

        return result

    def modify_stop_loss(self, ticker, order, price, comment = ""):
        TRADE_TRANS_INFO = {
            "cmd": 5,
            "customComment": comment,
            "expiration": 0,
            "offset": -1,
            "order": order,
            "price": price,
            "symbol": ticker,
            "type": 3,
            "volume": 0
        }
        message = {
	        "command": "tradeTransaction",
	        "arguments": {
		    "tradeTransInfo": TRADE_TRANS_INFO
	        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        print("Message received after SL modif : ", result)

        return result
        

    def check_take_profit(self, ticker, trades, SL_func):
        take_profit = 0
        sl_order = 0
        last_stop_loss = 0
        new_stop_loss = 0 
        ret = ""
        for trade in trades: 
            if trade['cmd'] == 5 and trade['symbol'] == ticker:
                sl_order = trade['order2']
                print("trade", trade)

                print("SL order", sl_order)
                last_stop_loss = trade['open_price']

            if trade['cmd'] == 0 and trade['symbol'] == ticker:        
                ## Closing position
                trade_info = self.get_trade_info(trade['order'])
                current_price = trade_info['returnData'][0]['close_price']

                if len(trade['customComment']) != 0: 
                    print("TP ", trade['customComment'], "ticker", ticker)
                    take_profit = float(trade['customComment'])
                    if current_price >= take_profit:

                        self.close_pkc(trade['position'], trade['symbol'], sl_order, trade['volume'])
                        ret = "position closed"
                ## Modifying stop loss 
                if ret == "":
                    new_stop_loss = SL_func(last_stop_loss, current_price, trade['open_price'])
                    self.modify_stop_loss(trade['symbol'], sl_order, round(new_stop_loss,2))
                    print("New stop loss", new_stop_loss)
                    ret = f"stop loss modified to: {new_stop_loss}"

        return ret

    def get_trades(self):
        message = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
        }
        }
        make_trade = json.dumps(message)
        result = self.send(make_trade)
        result = json.loads(result)

        result = sorted(result['returnData'], key=lambda x: x['cmd'], reverse= True)

        return result
    
    def get_trade_info(self, trade_orders):
        message = {
            "command": "getTradeRecords",
            "arguments": {
                "orders": trade_orders
        }
        }
        get_info = json.dumps(message)
        result = self.send(get_info)
        result = json.loads(result)

        return result

    def get_balance(self):
        command = {
	        "command": "getMarginLevel"
        }
         
        get_balance_json = json.dumps(command)
        result = self.send(get_balance_json)
        result = json.loads(result)
        

        return result['returnData']['equity'], result['returnData']['margin_free']

    
    def calc_position_size(self, risk, stock_price, total_capital, free):
        if free < 0: 
            print("No free funds shouldnt execute")
            free = 0
            return 0 
        
        total_usd_risk = total_capital * 0.02 # risk max 2% of capital for transaction
        risk_per_stock = stock_price * risk 
        no_stocks = math.floor (total_usd_risk / risk_per_stock)
    
        if no_stocks * stock_price > free: 
            no_stocks = math.floor(free / stock_price)


        return no_stocks
    



 