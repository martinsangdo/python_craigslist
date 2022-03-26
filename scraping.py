#!/usr/bin/env python
# coding=UTF-8
#http://lxml.de/lxmlhtml.html
from lxml import html

import requests
import time
from pymongo import MongoClient
import const_swipex
import calendar
import ssl
import sys

#parse detail page
def parse_detail_page(detail_page_url, detail):
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
    # print 'completed parse ' + detail_page_url
    scripts = tree.xpath('//script')
    valid_script = ''
    for script in scripts:
        if (script.text_content().find('var gid =') >= 0):
            valid_script = script.text_content()
            break
    # print valid_script
    lines = valid_script.splitlines()
    gid = ''
    uc = 0
    cover_url = ''
    for line in lines:
        line = line.strip()
        if (line.find('var gid =') >= 0):
            gid = line.replace('var gid =', '').replace(';', '')
        if (line.find('var uc =') >= 0):
            uc = line.replace('var uc =', '').replace(';', '')
        if (line.find('var img =') >= 0):
            cover_url = line.replace('var img =', '').replace(';', '').replace("'", '')
    detail['cover_url'] = cover_url.strip()
    if (gid != ''):
        page = ''
        url = 'https://www.javbus.com/ajax/uncledatoolsbyajax.php?lang=en&uc='+uc.strip()+'&gid='+gid.strip()
        while page == '':
            try:
                page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'referer': detail_page_url})
                break
            except:
                time.sleep(5)
                continue
        raw_data = html.fromstring(page.content)
        rows = raw_data.xpath('./tr')   #20210105 changed logic to get last row data
        detail['play_links'] = []
        detail['original_links'] = []
        if len(rows) > 0:
            tds = rows[len(rows)-1].xpath('./td')     #tds of last row
            if (len(tds) > 2):
                a_tag = tds[1].xpath('./a') #size
                detail['size'] = a_tag[0].text_content().strip()
                detail['play_links'] = [encrypt_str(a_tag[0].attrib['href'].strip())]   #encrypted magnet link
                #
                a_tag = tds[2].xpath('./a')
                detail['share_date'] = a_tag[0].text_content().strip()
                #save all links
                detail['original_links'] = []
                for row in rows:
                    row_data = {}
                    tds = row.xpath('./td')
                    a_tag = tds[0].xpath('./a')
                    row_data['title'] = a_tag[0].text_content().strip()
                    row_data['link'] = a_tag[0].attrib['href'].strip()   #magnet link, dont need to encrypt
                    a_tag = tds[1].xpath('./a')
                    row_data['size'] = a_tag[0].text_content().strip()
                    a_tag = tds[2].xpath('./a')
                    row_data['share_date'] = a_tag[0].text_content().strip()
                    detail['original_links'].append(row_data)
    #find thumbnails
    frames = tree.xpath('//div[@id="sample-waterfall"]/a[@class="sample-box"]')
    thumb_pics = []
    for frame in frames:
        thumb_pics.append(frame.get("href"))
    detail['thumb_pics'] = thumb_pics
    #find length of movie
    extra_info = tree.xpath('//div[@class="row movie"]/div[@class="col-md-3 info"]/p')
    if extra_info is not None and len(extra_info) > 2:
        detail['video_len'] = extract_numbers(extra_info[2].text_content().strip())
    #
    return
#######################
def extract_numbers(str):
    return ''.join([n for n in str if n.isdigit()])
#######################
#upsert movie detail
def upsert_detail(db_client, detail):
    #find if movie is existed (soft deleted or not)
    record = db_client[const_swipex.DB_COLLECTION_MOVIES].find_one({'code':detail['code']})
    if record is None:
        #not existed
        detail['created_time'] = getCurrentTimestamp()
        detail['source'] = 'javbus'
        detail['is_active'] = 0
        detail['is_processed_speed'] = 0
        detail['natural_order_index'] = -1
        detail['category_id'] = '5f75927b5c425008d254a788'    #censored
        detail['scanned_time'] = getCurrentTimestamp()
        db_client[const_swipex.DB_COLLECTION_MOVIES].insert_one(detail)
        # print('finish insert ====== ' + detail['code'])
    else:
        #existed in db, update original link data
        record['original_links'] = detail['original_links']
        record['video_len'] = detail['video_len']
        record['scanned_time'] = getCurrentTimestamp()
        #update empty play_links
        if len(record['original_links']) > 0:
            if record['play_links'] is None or record['play_links'] == '' or len(record['play_links']) == 0:
                record['play_links'] = [encrypt_str(record['original_links'][0]['link'])]
        db_client[const_swipex.DB_COLLECTION_MOVIES].update({'_id':record['_id']}, record)
        # print('finish update ' + detail['code'])
    return
#######################
def getCurrentTimestamp():
    return calendar.timegm(time.gmtime())
#######################
#encrypt string
def encrypt_str(original_str):
    lenx = len(original_str)
    #cut x characters at the end
    postfix_string = original_str[lenx - const_swipex.POST_ENCRYPT_LEN: lenx]
    #revert x characters
    revert_string = postfix_string[::-1]
    #remove post fix string
    cut_string = original_str[0: lenx - const_swipex.POST_ENCRYPT_LEN]
    #append revert string to the end
    return cut_string + revert_string
#######################
def parse_page(page_index):
    page = ''
    page_url = 'https://www.javbus.com/page/'+str(page_index)
    while page == '':
        try:
            page = requests.get(page_url, headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    tags = tree.xpath('//a[@class="movie-box"]')
    #traverve in revert order, latest movie should be on top
    for tag in tags[::-1]:
        # print tag.text_content()
        detail = {}
        detail['description'] = tag.xpath('./div/img')[0].attrib['title'].strip()
        detail['thumbnail'] = tag.xpath('./div/img')[0].attrib['src'].strip()
        detail['title'] = detail['code'] = tag.xpath('./div[@class="photo-info"]/span/date')[0].text_content().strip()
        if detail['code'] is not '':
            #parse detail of title page
            parse_detail_page(tag.attrib['href'], detail)
            # if detail['play_links'] is not '' and detail['play_links'] is not None and len(detail['play_links']) > 0:
            upsert_detail(db_client, detail)

#######################
#update detail of each movies (current time - latest_scan_update_time > 14 days)
def update_movies(db_client):
    current_time = getCurrentTimestamp()
    oldest_scan_time = current_time - 14*24*60*60   #14 days
    # print(oldest_scan_time)
    records = db_client[const_swipex.DB_COLLECTION_MOVIES].find({'source':'javbus',
                                                                 '$or':[{'scanned_time':None}, {'scanned_time':{'$lt':oldest_scan_time}}]}).sort("created_time", -1).limit(30)
    for saved_record in records:
        #parse detail of title page
        parse_detail_page('https://www.javbus.com/'+saved_record['code'], saved_record)
        upsert_detail(db_client, saved_record)
    return
#######################
start_time = getCurrentTimestamp()
# client = MongoClient('localhost:27017')
client = MongoClient('mongodb+srv://swipexdev2:fiptncjVopaaqAtU@cluster0.fwovj.mongodb.net', ssl_cert_reqs=ssl.CERT_NONE)
db_client = client['swipexdevdb']

start_page_index = 1    #from 1
end_page_index = 5

if (len(sys.argv) > 1):	#having parameter
    if sys.argv[1] == 'update':
        #update movies with links
        #python3 /home/ec2-user/python/swipex_python/parse_javbus_list.py update
        update_movies(db_client)
    else:   #scrape new movies
        #python3 /home/ec2-user/python/swipex_python/parse_javbus_list.py scrape 21 40
        if (len(sys.argv) > 3):
            start_page_index = int(sys.argv[2])
            end_page_index = int(sys.argv[3])
        while start_page_index <= end_page_index:
            parse_page(end_page_index)  #latest movies on top
            end_page_index = end_page_index - 1
#
end_time = getCurrentTimestamp()
total_time = end_time - start_time
# print('Total time: ' + str(total_time))
