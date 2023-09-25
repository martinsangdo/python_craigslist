from pymongo import MongoClient
from lxml import html
import requests
import os


#######################
def parse_page(db_collection, page_url):
    page = ''
    while page == '':
        try:
            page = requests.get(page_url, headers={'User-Agent': 'Mozilla/5.0'})
            break
        except:
            time.sleep(5)
            continue
    # print page.content
    tree = html.fromstring(page.content)
    content = tree.xpath('//div[@class="vocab-paragraphs"]')
    # print(content[0].text_content().strip())
    upsert_detail(db_collection, {
        "link": page_url,
        "en": content[0].text_content().strip(),
        "vi":""
    })
#######################
#upsert detail
def upsert_detail(db_collection, detail):
    record = db_collection.find_one({'link': detail['link']})
    if record is None:
        #not existed
        db_collection.insert_one(detail)
        print('Finish saving url: ' + detail['link'])
#######################
client = MongoClient('localhost:27017')
db_client = client['martin_projects']
db_collection = db_client['ielts_writing_task_2']

os.environ['no_proxy'] = '*'
session = requests.Session()
session.trust_env = False
proxies = {
    "http": None,
    "https": None,
}

page_urls = ["https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-14-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-13-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-09-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-08-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-07-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-05-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-03-01-2022-kem-bai-mau-sample-tu-vung","https://tuhocielts.dolenglish.vn//blog/de-thi-ielts-writing-task-2-ngay-02-01-2022-kem-bai-mau-sample-tu-vung"]

for page_url in page_urls:
    parse_page(db_collection, page_url)


