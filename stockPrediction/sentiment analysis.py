# -*- coding: utf-8 -*-
"""
Created on Sun Feb 17 13:18:37 2019

@author: deefunkt
"""
import time
import datetime as dt
import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib import style
from textblob import TextBlob

###############################################################################
'''Global conf variables '''
stock = ''
LOGFILE = 'sentiment_analysis.log'
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
    
    def writelog(self, log_string):
       self.f.write(log_string + '\n')
       print(log_string)
        
    def close_log(self):
        self.f.close()
        
###############################################################################
''' General method definitions '''

def preprocess_messages(messages):
    messages = messages.str.replace(REPLACE_WITH_SPACE, ' ', regex=True)
    messages = messages.str.replace(REPLACE_NO_SPACE, '',regex=True)
    messages[messages.isna()] = 'text'
    return messages
    
def get_sentiment(blob):
    return blob.sentiment.polarity

def get_subjectivity(blob):
    return blob.sentiment.subjectivity

###############################################################################
''' Initialization '''
timer = Timer()
logger = Logger(LOGFILE, one_time=True)

###############################################################################
''' Preprocessing stage '''
logger.writelog('Beginning preprocessing.')
REPLACE_NO_SPACE = re.compile("(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])")
REPLACE_WITH_SPACE = re.compile("(<br\s*/><br\s*/>)|(\-)|(\/)|(\.)")

timer.start()
df = pd.read_csv('Data/' + stock + '.csv', encoding = "cp1252")
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

ax1 = plt.subplot(2,1,1)
sentiments_date['sentiment'].plot(label = 'sentiment')
plt.legend()

ax2 = plt.subplot(2,1,2, sharex=ax1)
sentiments_date['subjectivity'].plot(label = 'subjectivity')
plt.legend()

plt.show()


logger.writelog('Preprocessing took {} seconds'.format(timer.elapsed_time()))

logger.close_log()
