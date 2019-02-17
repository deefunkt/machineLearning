# -*- coding: utf-8 -*-
"""
This file scrapes x for sentiment analysis.

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import csv
import re
import time
import datetime as dt

###############################################################################
# Variables set here are to be redacted for IP protection and privacy.
URL = ''
USERNAME = ''
PASSWORD = ''
STOCKS = []
DRIVER = webdriver.Chrome()
LOGFILE = 'Logs/last_run.log'

###############################################################################
''' CLASS DEFINITIONS '''
class Forum:
    def __init__(self, driver):
        self.driver = driver
        self.url = ''
        self.stock = ''
        self.threads = []
        self.username = ''
        self.password = ''
        self.num_posts = 0
        self.datafile = ''
    
    def set_user(self, username, password):
        self.username = username
        self.password = password
        logger.writelog('Username and Password set.')
    
    def set_url(self, url):
        self.url = url
        logger.writelog('Url set.')
    
    def set_stock(self, stock):
        self.stock = stock
        logger.writelog('Stock set.')
    
    def visit(self, page):
        try:
            self.driver.get(page)
            logger.writelog('Visiting {}'.format(page))
        except:
            logger.writelog('Unable to fetch {}'.format(page))
    
    def login(self):
        try:
            logger.writelog('Logging in.')
            elem = self.driver.find_element_by_id("login-register-btn")
            elem.click()
            elem = self.driver.find_element_by_id('ctrl_pageLogin_login')
            elem.send_keys(self.username)
            elem = self.driver.find_element_by_id('password')
            elem.send_keys(self.password)
            elem = self.driver.find_element_by_id('remember')
            if not elem.is_selected():
                self.driver.execute_script("arguments[0].click();", elem)
            elem = self.driver.find_element_by_id('tos')
            if not elem.is_selected():
                self.driver.execute_script("arguments[0].click();", elem)
            elem = self.driver.find_element_by_id('btn-login')
            elem.send_keys(Keys.RETURN)
        except Exception as e:
            if 'no such element' in e.args[0]:
                logger.writelog('Already Logged in. Proceeding.')
            else:
                logger.writelog('Unknown error:\n{0}'.format(e))
        

    def get_recent_links(self, extended=False):
        if extended:
            self.visit(self.url + '/asx/' + self.stock + '/discussion')
        else:
            self.visit(self.url + '/asx/' + self.stock + '/')
        logger.writelog(self.driver.current_url)
        # each row in 'latest threads' is of this class type.
        threads = self.driver.find_elements_by_class_name('subject-td')
        for elem in threads:
            try:
                page = elem.find_element_by_class_name('item-page-div')
                link = []
                for links in page.find_elements_by_xpath('.//a'):
                    link.append(links.get_attribute('href'))
            except:
                thread = elem.find_element_by_xpath('.//a')
                link = thread.get_attribute('href')  
            self.threads.append(link)
        logger.writelog('Getting the recently active pages.')
    
    
    def process_links(self, write2disk=True):
        if self.threads == []:
            return
        logger.writelog('Processing threads for {}'.format(self.stock))
        if write2disk:
            f = self.get_datafile()
            writer = csv.DictWriter(f, 
                                    fieldnames = ['date', 'time','thread','userid', 'user_rep', 'price', 'sentiment', 'disclosure','message'],
                                    delimiter=',', 
                                    quotechar='"', 
                                    quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            page_count = 1
            for thread in self.threads:
                try:
                    
                    if isinstance(thread, list):
                        for page in thread:
                            self.visit(page)
                            self.process_page(count = page_count, writer = writer)
                            page_count += 1
                    elif isinstance(thread, str):
                        self.visit(thread)
                        self.process_page(count = page_count, writer = writer)
                        page_count += 1
                    else:
                        logger.writelog('Unknown link format:{}\n{}'.format(type(thread),thread))
                except Exception as e:
                    logger.writelog('Thread {} returned the following error: \n{}'.format(thread, e.args[0]))
            f.close()
            logger.writelog('Closed file')
        else:
            logger.writelog('Write to disk is false, no logic implemented. Yet.')
    
    def count_threads(self):
        n_thr = 0
        for thread in self.threads:
            if type(thread) == list:
                n_thr += len(thread)
            else:
                n_thr += 1
        return n_thr
                
    def get_datafile(self):
        try:
            f = open('Data/'+self.stock+'.csv','r')
            f = open('Data/'+self.stock+'.csv','a')
            logger.writelog('Found and opened {}.csv datafile for append.'.format(self.stock))
        except:
            f = open('Data/'+self.stock+'.csv','w+')
            logger.writelog('Created {}.csv datafile.'.format(self.stock))
        finally:
            logger.writelog('Clearing old file contents.')
            f.seek(0)
            f.truncate()
        return f

    def process_page(self, count, writer=''):
        thread_title = self.driver.find_element_by_id('thread-title').text
        num_posts = 0
        logger.writelog('{0} Processing page: {1}'.format(count, thread_title))
        logger.writelog('Removing quoted messages')
        posts = self.driver.find_elements_by_class_name('post-message')
        logger.writelog('Found {} post elements.'.format(len(posts)))
        try:
            for post in posts:
                try:
                    self.driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, self.driver.find_element_by_class_name('attribution'))
                except:
                    pass
                num_posts += 1
                p = Post()
                p.parse_post(post)
                if writer != '':
                    to_write = p.__dict__
                    to_write['thread'] = thread_title
                    writer.writerow(to_write)
        except Exception as e:
            logger.writelog('Something went wrong:\n{}'.format(e))
        logger.writelog('Extracted {} posts.'.format(num_posts))
        self.num_posts += num_posts

class Post:
        
    def __init__(self):
        self.userid = ''
        self.user_rep = ''
        self.date = ''
        self.time = ''
        self.price = ''
        self.sentiment = ''
        self.disclosure = ''
        self.message = ''
        
        
    def parse_post(self, post):
        self.userid = re.findall('post-user-id-(.+)',post.get_attribute('class'))[0]
        try:
            self.user_rep = re.findall('\. (.+)',post.find_element_by_class_name('user-ga-count').text)[0]
        except:
            self.user_rep = 0
        self.date = post.find_element_by_class_name('post-metadata-date').text
        self.time = post.find_element_by_class_name('post-metadata-time').text
        meta = [p.text for p in post.find_elements_by_class_name('meta-details')]
        try:
            self.price = re.findall('\: (.+)',meta[0])[0]
            self.sentiment = re.findall('\: (.+)',meta[1])[0]
            self.disclosure = re.findall('\: (.+)',meta[2])[0]
        except:
            logger.writelog('Failed to extract post metadata price, sentiment or disclosure')
            self.price = 0
            self.sentiment = ''
            self.disclosure = ''
        self.message = post.find_element_by_class_name('message-text')
        self.message = self.message.text
        old = self.message #for debugging purposes
        self.sanitize_message()
        if self.message == '':
            logger.writelog('Couldnt parse: {}'.format(old))
    
    def sanitize_message(self):
        self.message = ''.join(re.findall('([^\\n][a-z A-Z0-9\.\,\?]+)', self.message))
        oc = re.findall('Originally posted by \w+: (.+)', self.message)
        if len(oc) > 0:
            self.message = ''.join(oc)

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
            

###############################################################################
'''GENERAL PURPOSE METHOD DEFINITIONS'''
def remove_element(parent, classnames):
    for c in classnames:
        element = parent.find_element_by_class_name(c)
        parent.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, element)
    return parent

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f,1):
            pass
    return i



def write_conf(stock, thread_count, num_posts, elapsed_time):
    today = dt.datetime.now().date()
    conf_dict = {
            'date_collected':today,
            'total_threads_parsed':thread_count, 
            'number_of_posts':num_posts,
            'time_taken_to_scrape':elapsed_time}
    with open('Logs/' + stock + '_run.csv', mode='w') as csv_file:
        logger.writelog('Clearing existing conf file if exists')
        csv_file.seek(0)
        csv_file.truncate()
        fieldnames = ['date_collected',
                      'total_threads_parsed', 
                      'number_of_posts', 
                      'time_taken_to_scrape']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(conf_dict)


###############################################################################
''' Initialization '''
timer = Timer()
logger = Logger(LOGFILE)
forum = Forum(DRIVER)


###############################################################################
''' MAIN CODE STARTS HERE. ALSO GOOD FOR PUTTING IN A __MAIN__ FUNCTION '''
forum.set_user(USERNAME, PASSWORD)
forum.set_url(URL)
forum.visit(forum.url)
forum.login()
time.sleep(5)
for stock in STOCKS:
    logger.writelog('MAIN: Fetching ' +  stock)
    timer.start()
    forum.set_stock(stock)
    forum.get_recent_links(extended=True)
    logger.writelog('MAIN: Found {} threads.'.format(forum.count_threads()))
    forum.process_links()
    logger.writelog('MAIN: Found {} posts.'.format(forum.num_posts))
    elapsed_time = timer.elapsed_time_string()
    write_conf(stock=stock,
               thread_count = forum.count_threads(),
               num_posts = forum.num_posts,
               elapsed_time = elapsed_time)


###############################################################################
''' Cleanup Operations '''
forum.driver.close()
logger.close_log()
