import plotly.graph_objects as go
import plotly.express as px 
import pandas as pd
import numpy as np

def candles_clean(zipped_list, lot_size):
    df = pd.DataFrame(zipped_list, columns = ['Date','Open','Close','High','Low'])
    df['Close'] = (df['Open'] + df['Close'])/lot_size
    df['High'] = (df['Open'] + df['High'])/lot_size
    df['Low'] = (df['Open'] + df['Low'])/lot_size
    df['Open'] = df['Open']/lot_size
    return df



def plot_candles(df, ma = 0):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
                ])
    if ma != 0:
        print("ELO")

    fig.show()


def plot_donchain(df):
    candlestick = go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
    line_up = go.Scatter(x=df['Date'], y =df['upper'], mode ='lines')
    line_low = go.Scatter(x=df['Date'], y =df['lower'], mode ='lines')

    fig = go.Figure(data = [candlestick, line_up, line_low])
    fig.show()


def plot_imp_areas(df):
    shapes = []
    candlestick = go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
    
    for i in df['important_area']:
        if not np.isnan(i): 
            shape = {
                'type': 'line',
                'x0': df['Date'].iloc[0],  # X-coordinate for the start of the line
                'x1': df['Date'].iloc[-1],  # X-coordinate for the end of the line
                'y0': i,  # Y-coordinate for the start of the line
                'y1': i,  # Y-coordinate for the end of the line
                'line': dict(color='red', width=2),  # Line color and width
            }
            shapes.append(shape)

    layout = go.Layout(shapes=shapes)

    fig = go.Figure(data = [candlestick], layout= layout)
    fig.show()


def plot_MACD(df):
    candlestick = go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])


    macd = go.Bar(x = df['Date'], y = df['profile'], marker=dict(color=['rgba(0, 255, 0, 0.7)' if val >= 0 else 'rgba(255, 0, 0, 0.7)' for val in df['profile']], line=dict(color=['green' if val >= 0 else 'red' for val in df['profile']],
                                    width=1.5)), yaxis='y2')
    layout = go.Layout(xaxis_rangeslider_visible=False, yaxis=dict(title='Candlestick Axis'))
    layout.update(yaxis2=dict(title='MACD Axis', overlaying='y', side='right', scaleratio = 0.1))
                  

    fig = go.Figure(data = [candlestick, macd], layout=layout)

    fig.show()


