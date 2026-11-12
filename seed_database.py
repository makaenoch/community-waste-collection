"""Load the original 20 fictional records into an empty local database."""
import os
from pathlib import Path
from pymongo import MongoClient
from bson import json_util

def main():
    root=Path(__file__).parent/'sample_data'
    collections=['households','collectors','collection_requests','payments']
    records={name:json_util.loads((root/(name+'.json')).read_text(encoding='utf-8')) for name in collections}
    client=MongoClient(os.getenv('MONGODB_URI','mongodb://127.0.0.1:27017'),serverSelectionTimeoutMS=5000)
    db=client[os.getenv('WASTE_DATABASE','enoch_1012_community_waste_midsem')]
    if any(db[name].count_documents({}) for name in collections):
        raise SystemExit('Import stopped: project records already exist. Nothing was changed. Use the existing database or select a new empty WASTE_DATABASE.')
    for name in collections:db[name].insert_many(records[name])
    db.payments.create_index('request_id',unique=True)
    db.collection_requests.create_index([('status',1),('requested_at',1)])
    db.collection_requests.create_index('household_id')
    for name in collections:print(name,db[name].count_documents({}))
    print('Original sample loaded: 20 fictional records, UGX 25,000 paid revenue.')

if __name__=='__main__':main()
