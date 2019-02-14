# -*- coding: utf-8 -*-
"""
This file scrapes x for sentiment analysis.

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import csv
import re
import pdb
import time
import datetime

# Variables set here are to be redacted for IP protection and privacy.
url = "x"
username = "x"
password = "x"
stocks = [x]

class Post:
        
    def __init__(self, post):
        self.userid = re.findall('post-user-id-(.+)',post.get_attribute('class'))[0]
        try:
            self.user_rep = re.findall('\. (.+)',post.find_element_by_class_name('user-ga-count').text)[0]
        except:
            self.user_rep = 0
        self.date = post.find_element_by_class_name('post-metadata-date').text
        self.time = post.find_element_by_class_name('post-metadata-time').text
        meta = [p.text for p in post.find_elements_by_class_name('meta-details')]
        self.price = re.findall('\: (.+)',meta[0])[0]
        self.sentiment = re.findall('\: (.+)',meta[1])[0]
        self.disclosure = re.findall('\: (.+)',meta[2])[0]
        self.message = post.find_element_by_class_name('message-text')
        try:
            self.message = remove_element(self.message, classnames = ['attribution','quoteContainer', 'bbCodeBlock']).text
        except:
            self.message = self.message.text
            pass
        self.message = self.sanitize_message()
        
    def sanitize_message(self):
        return ''.join(re.findall('([^\\n][a-z A-Z0-9\.\,\?]+)', self.message))
        

def remove_element(parent, classnames):
    for c in classnames:
        element = parent.find_element_by_class_name(c)
        parent.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, element)
    return parent
        

def login(driver, username, password):
    print('Logging in.')
    elem = driver.find_element_by_id("login-register-btn")
    elem.click()
    elem = driver.find_element_by_id('ctrl_pageLogin_login')
    elem.send_keys(username)
    elem = driver.find_element_by_id('password')
    elem.send_keys(password)
    elem = driver.find_element_by_id('remember')
    if not elem.is_selected():
        driver.execute_script("arguments[0].click();", elem)
    elem = driver.find_element_by_id('tos')
    if not elem.is_selected():
        driver.execute_script("arguments[0].click();", elem)
    elem = driver.find_element_by_id('btn-login')
    elem.send_keys(Keys.RETURN)

def get_recent_links(url, stock):
    thread_links = []
    driver.get(url + '/asx/' + stock)
    # each row in 'latest threads' is of this class type.
    threads = driver.find_elements_by_class_name('subject-td')
    for elem in threads:
        try:
            page = elem.find_element_by_class_name('item-page-div')
            link = []
            for links in page.find_elements_by_xpath('.//a'):
                link.append(links.get_attribute('href'))
        except:
            thread = elem.find_element_by_xpath('.//a')
            link = thread.get_attribute('href')  
        thread_links.append(link)
    return thread_links

def process_page(driver, write2disk=False):
    thread_title = driver.find_element_by_id('thread-title').text
    num_posts = 0
    print('Processing page: {}'.format(driver.title))
    if write2disk:
        try:
            f = open('Data/'+stock+'.csv','r')
            f = open('Data/'+stock+'.csv','a')
            writer = csv.DictWriter(f, 
                                fieldnames = ['date', 'time','thread','userid', 'user_rep', 'price', 'sentiment', 'disclosure','message'],
                                delimiter=',', 
                                quotechar='"', 
                                quoting=csv.QUOTE_MINIMAL)
        except:
            f = open('Data/'+stock+'.csv','w+')
            writer = csv.DictWriter(f, 
                                fieldnames = ['date', 'time','thread','userid', 'user_rep', 'price', 'sentiment', 'disclosure','message'],
                                delimiter=',', 
                                quotechar='"', 
                                quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
    posts = driver.find_elements_by_class_name('post-message')
    for post in posts:
        num_posts += 1
        p = Post(post)
        to_write = p.__dict__
        to_write['thread'] = thread_title
        if write2disk:
            writer.writerow(to_write)
    if write2disk: f.close()
    return num_posts
    
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f,1):
            pass
    return i

''' MAIN CODE STARTS HERE. ALSO GOOD FOR PUTTING IN A __MAIN__ FUNCTION'''
for stock in stocks:
    start_time = time.time()
    driver = webdriver.Chrome()
    driver.get(url)
    try:
        elem = driver.find_element_by_id("login-register-btn")
        login(driver, username, password)
    except Exception as e:
        if 'no such element' in e.args[0]:
            print('Already Logged in. Proceeding.')
        else:
            print('Unknown error:\n{0}'.format(e))
    threads = get_recent_links(url, stock)
    num_posts = 0
    num_threads = 0
    for thread in threads:
        if type(thread) == list:
            for page in thread:
                driver.get(page)
                num_threads += num_threads
                num_posts += process_page(driver,write2disk=True)
        elif type(thread) == str:
            driver.get(thread)
            num_threads += num_threads
            num_posts += process_page(driver,write2disk=True)
        else:
            print('Unknown link format:\n{0}'.format(thread))
    
    
    elapsed_time = time.time() - start_time
    d = datetime.timedelta(seconds= elapsed_time)
    d = datetime.datetime(1,1,1) + d
    elapsed_time = "%d days:%d hours:%d minutes:%d seconds" % (d.day-1, d.hour, d.minute, d.second)
    today = datetime.datetime.now().date()
    conf_dict = {
            'date_collected':today,
            'total_threads_parsed':num_threads, 
            'number_of_posts':num_posts, 
            'time_taken_to_scrape':elapsed_time}
    with open(stock + '.csv', mode='w') as csv_file:
        fieldnames = ['date_collected','total_threads_parsed', 'number_of_posts', 'time_taken_to_scrape']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
        writer.writeheader()
        writer.writerow(conf_dict)

driver.close()
