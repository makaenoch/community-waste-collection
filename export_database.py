"""Read-only export of the current local project, preserving BSON types."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
from pymongo import MongoClient
from bson import json_util

if __name__=='__main__':
    database=MongoClient('mongodb://127.0.0.1:27017',serverSelectionTimeoutMS=5000)['enoch_1012_community_waste_midsem']
    folder=Path(__file__).parent/'database-export'
    folder.mkdir(exist_ok=True)
    for name in ['households','collectors','collection_requests','payments']:
        records=list(database[name].find({}))
        (folder/(name+'.json')).write_text(json_util.dumps(records,indent=2),encoding='utf-8')
        print(f'{name}: exported {len(records)} records')
    print('Read-only export complete. No local records changed.')
