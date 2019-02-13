# -*- coding: utf-8 -*-
"""
This file scrapes x for sentiment analysis.

TODO; parse posts where they are quoting older posts.
TODO; remove newline and other special characters from posts before writing to disk

"""




from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import csv
import re
import pdb

# Variables set here are to be redacted for IP protection and privacy.
url = "x"
username = "x"
password = "x"
stock = 'x'

class Post:
        
    def __init__(self, post):
        self.userid = re.findall('post-user-id-(.+)',post.get_attribute('class'))[0]
        self.user_rep = re.findall('\. (.+)',post.find_element_by_class_name('user-ga-count').text)[0]
        self.date = post.find_element_by_class_name('post-metadata-date').text
        self.time = post.find_element_by_class_name('post-metadata-time').text
        meta = [p.text for p in post.find_elements_by_class_name('meta-details')]
        self.price = re.findall('\: (.+)',meta[0])[0]
        self.sentiment = re.findall('\: (.+)',meta[1])[0]
        self.disclosure = re.findall('\: (.+)',meta[2])[0]
        self.message = post.find_element_by_class_name('message-text').text
        

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
    if write2disk:
        f = open('Data/'+stock+'.csv','w+')
        writer = csv.DictWriter(f, 
                                fieldnames = ['date', 'time','userid', 'user_rep', 'price', 'sentiment', 'disclosure','message'],
                                delimiter=',', 
                                quotechar='"', 
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    posts = driver.find_elements_by_class_name('post-message')
    for post in posts:
        p = Post(post)
        if write2disk:
            writer.writerow(p.__dict__)
    if write2disk: f.close()
    

''' MAIN CODE STARTS HERE. ALSO GOOD FOR PUTTING IN A __MAIN__ FUNCTION'''
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

for thread in threads:
    if type(thread) == list:
        for page in thread:
            driver.get(page)

    elif type(thread) == str:
        driver.get(thread)
        process_page(driver,write2disk=True)
    else:
        print('Unknown link format:\n{0}'.format(thread))
driver.close()
