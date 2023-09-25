from pymongo import MongoClient



#######################
client = MongoClient('localhost:27017')
db_client = client['martin_projects']



db_collection = db_client['ielts_writing_task_1']

record = db_collection.find_one({'is_done': False})

print(record['vi'])
