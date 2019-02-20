# -*- coding: utf-8 -*-
"""
Created on Sun Feb 17 13:18:37 2019

@author: A-Sha
"""
import time
import datetime as dt
import pandas as pd
from glob import glob
import re
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.dates as mdates
from textblob import TextBlob

###############################################################################
'''Global conf variables '''
LOG_FILE = 'sentiment_analysis.log'
CONF_FILE = 'Conf/conf.csv'
DATAPATH = './Data/asxData/'
style.use('ggplot')

###############################################################################
''' Class definitions '''

class Timer:
    def __init__(self):
        self.start_time = 0
        
    def start(self):
        self.start_time = time.time()
        
    def elapsed_time(self):
        return time.time() - self.start_time
    
    def elapsed_time_string(self):
        elapsed_time = time.time() - self.start_time
        d = dt.timedelta(seconds= elapsed_time)
        d = dt.datetime(1,1,1) + d
        elapsed_time = "%d days:%d hours:%d minutes:%d seconds" % (d.day-1, d.hour, d.minute, d.second)
        return elapsed_time
    
class Logger:
    def __init__(self, logfile, one_time=False):
        self.f = open(logfile, 'w+')
        if one_time:
            self.f.seek(0)
            self.f.truncate()
        self.f.write(str(dt.datetime.now()) + '\n')
        self.f.write('##############################')
        self.conf_dict = {}
    
    def writelog(self, log_string):
       self.f.write(log_string + '\n')
       print(log_string)
        
    def close_log(self):
        self.f.close()
        
    def read_conf(self,conf_file='Conf/conf.csv'):
        self.conf_dict = pd.read_csv(conf_file, delimiter=',')
    
###############################################################################
''' General method definitions '''

def preprocess_messages(messages):
    REPLACE_NO_SPACE = re.compile("(\$)|(\+)|(@)|(%)|(\;)|(\:)|(\!)|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])|([0-9]+)")
    REPLACE_WITH_SPACE = re.compile("(<br\s*/><br\s*/>)|(\-)|(\/)|(\.)")
    contr_dict={"I'm": "I am",
            "won't": "will not",
            "'s" : "", 
            "'ll":" will",
            "'ve":" have",
            "n't":" not",
            "'re": " are",
            "'d": " would",
            "y'all": "all of you"}
    messages = messages.str.replace(REPLACE_WITH_SPACE, ' ', regex=True)
    messages = messages.str.replace(REPLACE_NO_SPACE, ' ',regex=True)
    messages = messages.str.replace('\s{2,}', ' ', regex=True)
    messages = messages.str.lower()
    messages[messages.isna()] = 'text'
    return messages

def stock_data_import(path):
    csv_files = glob(path + '*/*', recursive=True)
    csv_files.sort()
    rawdata = []
    for i in range(0, len(csv_files)):
        temp_cv = pd.read_csv(csv_files[i], header=0, index_col=0,
                              names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
                              parse_dates=['Date'])
        try:
            rawdata.append(temp_cv.loc[stock])
        except KeyError:
            try:
                rawdata.append(temp_cv.loc[altname])
            except:
                pass
            print(stock + " not found at " + str(temp_cv['Date'][0].date()))
    processed_data = pd.DataFrame(rawdata)
    processed_data = processed_data.reset_index(drop=True)
    processed_data.set_index('Date', inplace=True)
    # currently in format [Open, High, Low, Close, Volume].
    # We reorganize:
    cols = ['Open', 'High', 'Low', 'Volume','Close']
    processed_data = processed_data[cols]
    print('End of data import.')
    return processed_data
    

def get_sentiment(blob):
    return blob.sentiment.polarity

def get_subjectivity(blob):
    return blob.sentiment.subjectivity

###############################################################################
''' Initialization '''
timer = Timer()
logger = Logger(LOG_FILE, one_time=True)
logger.read_conf()
stock = 'KRR'
altname= 'KRC'
timer.start()
stock_data = stock_data_import(DATAPATH)
logger.writelog('Importing ASX data took {} seconds'.format(timer.elapsed_time()))
df = pd.read_csv('Data/' + stock + '.csv', encoding = "cp1252")
###############################################################################
''' Preprocessing stage '''
logger.writelog('Beginning preprocessing.')


timer.start()

df['datetime'] = df['date'] + ' ' + df['time']
df.set_index('datetime', inplace=True)
df.drop(['date','time'], inplace=True, axis=1)
df.index = pd.to_datetime(df.index, errors='coerce')
df = df[pd.notnull(df.index)]
df['message'] = preprocess_messages(df['message'])
df['textblob'] = df['message'].apply(TextBlob)
df['sentiment'] = df.textblob.apply(get_sentiment)
df['subjectivity'] = df.textblob.apply(get_subjectivity)
sentiments_date = pd.DataFrame(columns = ['sentiment', 'subjectivity'], index=pd.unique(df.index.date))
sentiments_date.index = pd.to_datetime(sentiments_date.index)
sentiments_date['day'] = sentiments_date.index.day_name()
for index, value in sentiments_date.iterrows():
    sentiments_date.loc[index, 'sentiment'] = df.sentiment[df.index.date == index.date()].mean()
    sentiments_date.loc[index, 'subjectivity'] = df.subjectivity[df.index.date == index.date()].mean()
logger.writelog('Preprocessing took {} seconds'.format(timer.elapsed_time()))



ax3 = plt.subplot(3,1,1)
stock_data['Close'].plot( label = stock + ' Close', )
plt.legend()
ax2 = plt.subplot(3,1,2)
sentiments_date['subjectivity'].plot(label = 'subjectivity', sharex=ax3)
plt.legend()
ax1 = plt.subplot(3,1,3)
sentiments_date['sentiment'].plot(label = 'sentiment', sharex=ax3)
plt.legend()




#set major ticks format


plt.show()

logger.close_log()
