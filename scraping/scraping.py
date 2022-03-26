#!/usr/bin/env python
# coding=UTF-8
#http://lxml.de/lxmlhtml.html
from lxml import html

import requests
import time
from pymongo import MongoClient
import constant
import calendar
import ssl
import sys

#######################
def getCurrentTimestamp():
    return calendar.timegm(time.gmtime())
#######################
#parse detail page
def parse_detail_page(db_client, meta_detail, detail, detail_page_url):
    page = ''
    while page == '':
        try:
            page = requests.get(detail_page_url, headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    detail['url'] =  detail_page_url
    # print 'completed parse ' + detail_page_url
    #get title
    title = tree.xpath('//span[@class="postingtitletext"]')
    detail['title'] = title[0].text_content().strip()
    #get description
    description = tree.xpath('//section[@id="postingbody"]')
    detail['description'] = html.tostring(description[0])
    #get extra info
    extra_info = tree.xpath('//p[@class="attrgroup"]')
    detail['extra_info'] = html.tostring(extra_info[0])
    #
    detail['country'] = meta_detail['country']
    detail['city'] = meta_detail['city']
    detail['catalog'] = meta_detail['catalog']
#
    upsert_detail(db_client, detail)

    return
#######################
#parse post list page
def parse_post_list_page(db_client, meta_detail, post_list_page_url):
    page = ''
    while page == '':
        try:
            page = requests.get(post_list_page_url+'?employment_type=2&employment_type=3&employment_type=4', headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    print 'completed parse ' + post_list_page_url
    list = tree.xpath('//ul[@id="search-results"]/li[@class="result-row"]')
    for item in list:
        detail = {}
        #find date
        date = item.xpath('.//time[@class="result-date"]')
        detail['datetime'] = date[0].attrib['datetime']
        #find link
        link = item.xpath('.//a')
        parse_detail_page(db_client, meta_detail, detail, link[0].attrib['href'])
    return
#######################
#parse city page
def parse_city_page(db_client, meta_detail, city_page_url):
    page = ''
    while page == '':
        try:
            page = requests.get(city_page_url, headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    # print 'completed parse ' + city_page_url
    software = tree.xpath('//a[@class="sof"][@data-cat="sof"]')
    meta_detail['catalog'] = 'software';
    parse_post_list_page(db_client, meta_detail, city_page_url.replace('craigslist.org/', 'craigslist.org') + software[0].attrib['href'])
    #web design
    web = tree.xpath('//a[@class="web"][@data-cat="web"]')
    parse_post_list_page(db_client, meta_detail, city_page_url.replace('craigslist.org/', 'craigslist.org') + web[0].attrib['href'])
    return
#######################
#upsert movie detail
def upsert_detail(db_client, detail):
    # print(detail)
    # print('--------')
    #find if movie is existed (soft deleted or not)
    record = db_client[constant.DB_COLLECTION_POST].find_one({'url':detail['url']})
    if record is None:
        #not existed
        detail['created_time'] = getCurrentTimestamp()
        db_client[constant.DB_COLLECTION_POST].insert_one(detail)
        # print('finish insert ====== ' + detail['code'])
    return
#######################
def parse_page():
    page = ''
    page_url = constant.MAIN_HOMEPAGE
    while page == '':
        try:
            page = requests.get(page_url, headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    rightbar = tree.xpath('//div[@id="rightbar"]')
    lis = rightbar[0].xpath('.//a')
    # print (len(lis))
    #traverse each continent
    for country in lis:
        # print(country.attrib['href'])
        href = country.attrib['href']
        if (href.find('.craigslist.org') > 0):
            if (href.find('/about/sites') > 0):
                parse_country_page(country.attrib['href'], country.text_content())
            else:
                parse_about_page(country.attrib['href'])

#######################
start_time = getCurrentTimestamp()
client = MongoClient('localhost:27017')
db_client = client['craigslist_db']

# parse_page()

#test
meta_detail = {}
meta_detail['city'] = 'los angeles'
meta_detail['country'] = 'americas'
parse_city_page(db_client, meta_detail, 'https://losangeles.craigslist.org')
#
end_time = getCurrentTimestamp()
total_time = end_time - start_time
# print('Total time: ' + str(total_time))
