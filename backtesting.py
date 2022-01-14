import datetime as dt
import yfinance as yf
from pandas_datareader import data as pdr
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

#Initializing data needed for strategy.
yf.pdr_override()
stock="TSLA"
start=dt.datetime(2021,1,1)
end=dt.datetime.now()

df=pdr.get_data_yahoo(stock,start,end)

df['EMA_12']=df.iloc[:,4].ewm(span=12, adjust=False).mean()
df['EMA_26']=df.iloc[:,4].ewm(span=26, adjust=False).mean()
df['MACD']=df.iloc[:,6]-df.iloc[:,7]
df['SIGNAL']=df.iloc[:,8].ewm(span=9, adjust=False).mean()
df['DIFFSM']=df.iloc[:,8]-df.iloc[:,9]

#Setting up variables to tract the progress of trading strategy and anything else needed for the strategy.
holding=False
loc=0
res=[]
buyingPrice = -1
lenDF = df["MACD"].count()


BuyDate=[]
BuyPrice=[]
SellDate=[]
SellPrice=[]

#print(df.tail())
#Running the strategy through the dataset.
for i in df.index:
    close = df["Close"][i]
    currMacd = df["MACD"][i]
    currSignal = df["SIGNAL"][i]
    
    if (currMacd > currSignal):
        if not holding:
            holding = True
            buyingPrice = close
            BuyDate.append(i)
            BuyPrice.append(buyingPrice)
    elif (currMacd < currSignal):
        if holding:
            holding = False
            gain = 100 * (close - buyingPrice)/buyingPrice
            SellDate.append(i)
            SellPrice.append(close)
            res.append(round(gain,3))
    
    if (loc == lenDF - 1 and holding):
        holding = False
        gain = 100 * (close - buyingPrice)/buyingPrice
        SellDate.append(i)
        SellPrice.append(close)
        res.append(round(gain,3))
    
    loc += 1
    
df.insert(11,"Date",df.index, False)

#Calculating %profit and other useful stai
maxReturn = res[0]
maxDate = str(SellDate[0])
avgReturn = sum(res)/len(res)
for i in range(1,len(res)):
    if res[i] > maxReturn:
        maxReturn = res[i]
        maxDate = str(SellDate[i])


#print(df.head())
print("Max Return on " + maxDate + " earning a gain of " + str(round(maxReturn,2)) + "%.")
print("This strategy earned an average return of " + str(round(avgReturn,2)) + "% by placing " + str(len(res)) + " trades from " + str(start) + " to " + str(end) +".") 

candlestickFig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])])
EMA_12Fig = px.line(df, x='Date', y="EMA_12")
EMA_12Fig.update_traces(line=dict(color = 'rgba(238,130,238,0.7)'))
EMA_26Fig = px.line(df, x='Date', y="EMA_26")
BuyFig = go.Figure(data=go.Scatter(x=BuyDate, y=BuyPrice, mode='markers'))
BuyFig.update_traces(marker=dict(color = 'rgba(60, 179, 113,1)', size=9, line=dict(width=1,
                                        color='DarkSlateGrey')))
SellFig = go.Figure(data=go.Scatter(x=SellDate, y=SellPrice, mode='markers'))
SellFig.update_traces(marker=dict(color = 'rgba(255, 0, 0,1)', size=9, line=dict(width=1,
                                        color='DarkSlateGrey')))
topFig = go.Figure(data=EMA_12Fig.data + EMA_26Fig.data + candlestickFig.data + BuyFig.data + SellFig.data)
topFig.update_layout(xaxis_rangeslider_visible=False)


macDFig=px.line(df, x='Date', y="MACD")
signalFig=px.line(df, x='Date', y="SIGNAL")
signalFig.update_traces(line=dict(color = 'rgba(255,165,0,0.7)'))
df["Color"]=np.where(df["DIFFSM"]<0, 'rgb(255, 0, 0)', 'rgb(60, 179, 113)')
DiffFig = go.Figure()
DiffFig.add_trace(
    go.Bar(x=df['Date'],
           y=df['DIFFSM'],
           marker_color=df['Color']))
DiffFig.update_layout(barmode='stack')
botFig=go.Figure(data=macDFig.data + signalFig.data + DiffFig.data)

combinedFig = make_subplots(rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.02,
                    row_heights=[0.7,0.3],
                    shared_yaxes=False)

#EMA_12Fig = px.l
for i in range(len(topFig.data)):
    combinedFig.add_trace(topFig.data[i], row=1, col=1)
for i in range(len(botFig.data)):
    combinedFig.add_trace(botFig.data[i], row=2, col=1)
combinedFig.update_layout(xaxis_rangeslider_visible=False)
combinedFig.update_xaxes(range=[start, end], row=2, col=1)
combinedFig.show()