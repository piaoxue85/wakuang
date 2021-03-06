
import talib
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time

#import st_imformation as sti
today=datetime.date.today()   # setup date

def get_date_ts(Code,startDate,endDate):#获取开始数据
    """
    get code date from web.Use tushare get_k_data fuction.


    Parameters
    ----------
    Code: 
    startDate: 
    endDate: 

    Returns
    ------- 
    df: DateForm 
    index   open   close   high  low  volume  code  
    date                                                            

    """
    df=ts.get_k_data(Code,startDate,end=endDate)
    df=df.reset_index()
    df=df.sort_index(ascending=True)# 从后倒序
    df.date=df.date.apply(lambda x:datetime.datetime.strptime(x,"%Y-%m-%d"))
    df=df.set_index('date') # 设置 index 成 date
    if endDate == '%s'%today:# deal today datas
        RealTimeList=ts.get_realtime_quotes(Code)
      
        df.loc['%s'%today,'close']=float(RealTimeList.price)
        df.loc['%s'%today,'open']=float(RealTimeList.open)
        df.loc['%s'%today,'high']=float(RealTimeList.high)
        df.loc['%s'%today,'low']=float(RealTimeList.low)
        df.loc['%s'%today,'volume']=float(RealTimeList.volume)
    return df

def myMACD(price, fastperiod=10, slowperiod=20, signalperiod=9):
    price=pd.Series(price)
    ewma12 = price.ewm(span=fastperiod).mean()
    ewma60 = price.ewm(span=slowperiod).mean()
    dif = ewma12-ewma60
    dea = dif.ewm(span=signalperiod).mean()
    bar = (dif-dea) #有些地方的bar = (dif-dea)*2，但是talib中MACD的计算是bar = (dif-dea)*1
    return dif,dea,bar

def draw_macd(code,starttime,endtime):

    
    df=get_date_ts(code,starttime,endtime)

    #macd, signal, hist = talib.MACD(df['close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

    #三个指数都为正
    macd, signal, hist = myMACD(df['close'].values, fastperiod=10, slowperiod=20, signalperiod=9)
    ax1=plt.subplot(111)


    plt.plot(df.index,df.close,"y")
    #plt.ylim(df.close.min()-3, df.close.max()+1)
    
    ax2=ax1.twinx()
    plt.plot(df.index,macd,'r',label='macd dif')   
    plt.plot(df.index,signal,'b',label='signal dea')
    #plt.bar(df.index,hist,'g',label='hist bar')
    plt.plot(df.index,0*df.open,'--')
   # plt.ylim(-1, 3)
    plt.legend(loc='best')
    plt.grid(True)
    

def ewma_day(code_list,days_=30): # 30day EWMA走线
    
    startday=today-datetime.timedelta(days=days_*2)
    
    datas_sh=ts.get_hist_data('sh',start='%s'%startday,end='%s'%today)
  
    every_day=datas_sh.close
    every_day=every_day.reset_index()
    
    every_day=every_day.rename(columns={'close':'szzs'})
    
    for code_ in code_list[1:]:
        datas=ts.get_hist_data(code_,start='%s'%startday,end='%s'%today)    
        every_day1=datas.close
        ewma30 = pd.ewma(every_day1.values,span=days_)
        every_day1=pd.Series(data=ewma30,index=every_day1.index,name=code_)
        every_day1=every_day1.reset_index()
        every_day=pd.merge(every_day,every_day1,on='date',how='outer')

    every_day.date=every_day.date.apply(lambda x:datetime.datetime.strptime(x,"%Y-%m-%d"))
    every_day=every_day.set_index('date')#设置日期轴
    every_day=every_day.sort_index(ascending= False)# 从后倒序

    return every_day
'''
布林线上下轨
'''
def ST_bands (code,startday,enday,tp=14):
    '''
    upperband   , 上轨  均线加一倍标准差
    middleband  ，中轨  均线
    lowerband   ，下轨  均线减一倍标准差

    '''
    
    df=get_date_ts(code,startday,enday)
    
    upperband, middleband, lowerband = talib.func.BBANDS(df.close.values, timeperiod=tp, nbdevup=2, nbdevdn=2, matype=0)

    df['upperband']=upperband
    df['middleband']=middleband
    df['lowerband']=lowerband
    #print(df)
    return df

def draw_bands(df):
    plt.plot(df.index,df.close,'b')
    plt.plot(df.index,df.upperband,'r')
    plt.plot(df.index,df.middleband,'k')
    plt.plot(df.index,df.lowerband,'r')
    plt.legend(loc='best')
    plt.grid(True)


def VWAP(code='sz',startday='2015-01-05',enday='2016-12-21'):# price 加权平均指标
   
    
    
    SQ={'slower_line':24,'middler_line':6,'fast_line':2}
    if code == 'sh':
        SQ['slower_line']=12

    df=get_date_ts(code,startday,enday)
    df['pvc']=df.close*df.volume

    
    if enday == '%s'%today:
        realtime_price=ts.get_realtime_quotes(code).price
        realtime_price=float(realtime_price)
        print('当前价格：%s'%realtime_price)
        df.loc['%s'%today,'close']=realtime_price
    for name in SQ:
        values=SQ['%s'%name]
        #print(values)
        cnt = 0
        for i in df.index[values-1:]:
            pv_sum=df[cnt:cnt+values].pvc.sum()
            vlo_sum=df[cnt:cnt+values].volume.sum()
            df.loc[i,'%s'%name]=pv_sum/vlo_sum
            cnt= cnt+1
    return df

def draw_VWAP(df): # 画加权平均指数
      
    plt.plot(df.index,df.close,'R',linewidth=2.0)
    plt.plot(df.index,df.slower_line,'B')
    plt.plot(df.index,df.middler_line,'orange')
    plt.plot(df.index,df.fast_line,'g')
    plt.legend(loc='best')
    plt.grid(True) 
    
'''
RSI强弱指标
'''
    
def RSI(code='sh',startday='2015-01-05',enday='2016-12-21',timeperiod=10):# price 加权平均指标    
    #timeperiod=1
    if code == 'sh':
        timeperiod=10
    df=get_date_ts(code,startday,enday)
    df['RSI']=talib.func.RSI(df.close.values,timeperiod)#调用RSI函数计算RSI  因子设为10
    
    return df

def draw_RSI(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"k")
    #plt.ylim(df.close.min()-3, df.close.max()+1)
    ax2=ax1.twinx()

    plt.plot(df.index,df.RSI,'-',c='y',label='RSI')    


    plt.plot(df.index,0*df.open+20,'--')
    plt.plot(df.index,0*df.open+50,'--')
    plt.plot(df.index,0*df.open+80,'--')
   # plt.ylim(-1, 3)
    plt.legend(loc='best')#输出标签，保持在最优模式
    plt.grid(True)
    
def ADX(code='sh',startday='2015-01-05',enday='2016-12-21'):# ADX  多空占比   
    df=get_date_ts(code,startday,enday)
    #print(df)
    df['ADX']=talib.func.ADX(high=df.high.values,low=df.low.values,close=df.close.values,timeperiod=10)
    #多空比率净额= [（收盘价－最低价）－（最高价-收盘价）] ÷（ 最高价－最低价）×V
    return df
def draw_ADX(df): # 画加权平均指数
    ax1=plt.subplot(111)      
    plt.plot(df.index,df.close,"b")
    x2=ax1.twinx()
    plt.plot(df.index,df.ADX,'g',label='ADX')    
    plt.legend(loc='best')
    plt.grid(True)
    
def ADOSC(code='sh',startday='2015-01-05',enday='2016-12-21',f=5,s=30):# 量价分析资金流入流出
    #timeperiod=1
    # if code == 'sh':
    #    timeperiod=10
    df=get_date_ts(code,startday,enday)

    df['ADOSC']=talib.func.ADOSC(high=df.high.values,
                          low=df.low.values,
                          close=df.close.values,
                          volume=df.volume.values,
                          fastperiod=f,
                          slowperiod=s)


    return df


def draw_ADOSC(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"b")
    x2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.ADOSC,'g',label='ADOSC')    
    plt.legend(loc='best')
    plt.grid(True)
    
#TODO:  this funcation is not adjust the timeperiod . 
def MFI(code='sh',startday='2015-01-05',enday='2016-12-21',day=14):# MFI - Money Flow Index 
    df=get_date_ts(code,startday,enday)
    df['MFI']=talib.func.MFI(high=df.high.values,
                          low=df.low.values,
                          close=df.close.values,
                          volume=df.volume.values,
                          timeperiod=day)
    return df
def draw_MFI(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"b")
    x2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.MFI,'r',label='CCI')    
    plt.legend(loc='best')
    plt.grid(True)
    
'''
Hilbert Transform - HT_TRENDLINE 
Such as K LINE, to comput the volume. 
有效，不明确
'''
#TODO:  this funcation is not adjust the timeperiod . 
def Hilbert(code='sh',startday='2015-01-05',enday='2016-12-21'):
    df=get_date_ts(code,startday,enday)
    df['Hilbert']=talib.func.HT_TRENDMODE(df.close.values)
    return df
def draw_Hilbert(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"g")
    x2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.Hilbert,'r',label='Hilbert')    
    plt.legend(loc='best')
    plt.grid(True)
'''
Parabolic SAR
Such as K LINE, to comput the volume. 
有效，不明确
'''
#TODO:  this funcation is not adjust the timeperiod . 
def SAR(code='sh',startday='2015-01-05',enday='2016-12-21'):
    df=get_date_ts(code,startday,enday)
    df['SAR']=talib.func.SAR(df.high.values,df.low.values,acceleration=0.02, maximum=0.2)
    return df
def draw_SAR(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"g")
  #  x2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.SAR,'r',label='Parabolic SAR')    
    plt.legend(loc='best')
    plt.grid(True)

'''
funcdation : CCI 顺势指标 并不是很准
'''
#TODO: this funcation is not adjust the timeperiod . 
def CCI(code='sh',startday='2015-01-05',enday='2016-12-21',tp=11):
    df=get_date_ts(code,startday,enday)
    df['CCI']=talib.func.CCI(df.high.values,df.low.values,df.close.values,timeperiod=tp)
    return df
def draw_CCI(df): # 画加权平均指数
    ax1=plt.subplot(111)
      
    plt.plot(df.index,df.close,"g")
    ax2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.CCI,'r',label='Commodity channel index') 

    plt.plot(df.index,df.CCI.values*0+100,"B",label="+") 
    plt.plot(df.index,df.CCI.values*0-100,"B",label="-")     
    plt.legend(loc='best')
    plt.grid(True)   

#TODO: timeperiod need adjusts
def AROON(code='sh',startday='2015-01-05',enday='2016-12-21',tp=25):
    """
    AROON is like RSI
    docstring here
        :param code:  stock code
        :param startday: start of date
        :param enday: end of date
        :param tp: tp is timeperiod 
    out put:
        dateform as df
    """
    
    df=get_date_ts(code,startday,enday)
    
    aroonup,aroondown=talib.AROON(df.high.values,df.low.values,timeperiod=tp)
    df['aroondown']=aroondown
    df['aroonup']=aroonup

    return df
def draw_AROON(df): 
    ax1=plt.subplot(111)
    plt.plot(df.index,df.close,"g")
    ax2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.aroondown,'r',label='DOWN')
    plt.plot(df.index,df.aroonup,'b',label='UP')  
    plt.legend(loc='best')
    plt.grid(True)

#TODO: timeperiod need adjusts ;AROONOSC 比 AROON更加有效，可以结合RSi使用
def AROONOSC(code='sh',startday='2015-01-05',enday='2016-12-21',tp=15):
    """
    AROONOSC is like RSI 阿隆正当指数  +/- 100 上下波动
    docstring here
        :param code:  stock code of 
        :param startday: start of date
        :param enday: end of date
        :param tp: tp is timeperiod 
    out put:
        dateform as df
    """
    
    df=get_date_ts(code,startday,enday)
    df['aroon']=talib.AROONOSC(df.high.values,df.low.values,tp)
   
    return df
def draw_AROONOSC(df): 
    """
    docstring here
        :param df: the data form is pandas 
    """
    ax1=plt.subplot(111)
    plt.plot(df.index,df.close,"g")
    ax2=ax1.twinx()#设立爽坐标
    plt.plot(df.index,df.aroon,'r',label='DOWN') 
    plt.legend(loc='best')
    plt.grid(True)
    
if __name__=="__main__":
    plt.close()
   #399006 
    '''
   INDEX_LIST = {'sh': 'sh000001', 
                 'sz': 'sz399z001',
                 'hs300': 'sz399300',
                 'sz50': 'sh000016',
                 'zxb': 'sz399005', 
                 'cyb': 'sz399006',
                 'zx300': 'sz399008', 
                 000976 000929 000911 000639 601139
                 'zh500':'sh000905'}
    '''
    code_="600352"
    start_='2017-06-01'
    end_='%s'%today 
    #end_="2018-09-03"
    print(end_)

    plt.figure(1) 
    VW=VWAP(code_,start_,end_) 
    draw_VWAP(VW)
    
    plt.figure(2)
    brand=ST_bands(code_,start_,end_)
    draw_bands(brand)
    
    plt.figure(3)
    draw_macd(code_,start_,end_)
    plt.figure(4)
    RSI_IDEX=RSI(code_,start_,end_)
    draw_RSI(RSI_IDEX)
    plt.figure(5)
    ARC_INDEX=AROONOSC(code_,start_,end_)
    draw_AROONOSC(ARC_INDEX)
 #   plt.figure(5)
 #   ADX_IDEX=ADX(code_,start_,end_)
 #   draw_ADX(ADX_IDEX)#ADX 非相关重要信息
    plt.figure(6)
    ADOSC_IDEX=ADOSC(code_,start_,end_)
    
    draw_ADOSC(ADOSC_IDEX)
     
    plt.show()

