import sys, os, json, secrets, threading, webbrowser
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
sys.path.insert(0, str(Path(__file__).parent / 'vendor'))
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

ROOT = Path(__file__).parent
DB_NAME = os.getenv('WASTE_DATABASE', 'enoch_1012_community_waste_midsem')
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017'), serverSelectionTimeoutMS=4000)
db = client[DB_NAME]
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
COLLECTIONS = ['households', 'collectors', 'collection_requests', 'payments']
DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

def text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
        raise ValueError(f'Enter a valid {key.replace("_", " ")} (maximum 200 characters).')
    return value.strip()

def choice(data, key, options):
    value = text(data, key)
    if value not in options: raise ValueError(f'Invalid {key}.')
    return value

def number(data, key):
    value = data.get(key)
    if isinstance(value, bool): raise ValueError(f'{key} must be a positive whole number.')
    try: value = int(str(value))
    except (ValueError, TypeError): raise ValueError(f'{key} must be a positive whole number.')
    if value < 1 or value > 1000000000: raise ValueError(f'{key} is outside the allowed range.')
    return value

def build_document(kind, data):
    prefix = {'households':'H','collectors':'C','collection_requests':'R','payments':'P'}[kind]
    doc = {'_id': prefix + '_' + secrets.token_hex(6).upper()}
    if kind == 'households':
        doc.update(name=text(data,'name'), area=text(data,'area'), location={'zone':text(data,'zone'),'landmark':text(data,'landmark')}, preferred_day=choice(data,'preferred_day',DAYS))
    elif kind == 'collectors':
        areas = [a.strip() for a in text(data,'service_areas').split(',') if a.strip()]
        if not areas: raise ValueError('Enter at least one service area.')
        doc.update(name=text(data,'name'),service_areas=areas,vehicle_code=text(data,'vehicle_code'),active=True)
    elif kind == 'collection_requests':
        h = db.households.find_one({'_id':text(data,'household_id')})
        c = db.collectors.find_one({'_id':text(data,'collector_id')})
        if not h or not c: raise ValueError('Choose an existing household and collector.')
        if not c.get('active') or h['area'].casefold() not in [a.casefold() for a in c['service_areas']]:
            raise ValueError('Choose an active collector who serves the household area.')
        doc.update(household_id=h['_id'],collector_id=c['_id'],waste_type=choice(data,'waste_type',['organic','mixed','plastic','paper','metal','glass']),bags=number(data,'bags'),requested_at=datetime.now(timezone.utc),status='pending')
    else:
        request = db.collection_requests.find_one({'_id':text(data,'request_id')})
        if not request: raise ValueError('Choose an existing pickup request.')
        status = choice(data,'status',['paid','unpaid'])
        doc.update(request_id=request['_id'],household_id=request['household_id'],amount_ugx=number(data,'amount_ugx'),method=choice(data,'method',['cash','mobile_money','bank_transfer']),status=status,paid_at=datetime.now(timezone.utc) if status=='paid' else None)
    return doc

def create(kind, data):
    doc=build_document(kind,data)
    db[kind].insert_one(doc)
    return doc

def edit(kind,data):
    ident=text(data,'id')
    old=db[kind].find_one({'_id':ident})
    if not old: raise ValueError('Record no longer exists. Refresh the records.')
    doc=build_document(kind,data)
    doc.pop('_id')
    if kind=='households':
        if doc['area']!=old['area'] and db.collection_requests.find_one({'household_id':ident}):
            raise ValueError('This household has pickup requests. Its area cannot be changed while those requests exist.')
    elif kind=='collectors':
        active=choice(data,'active',['true','false'])=='true'
        for job in db.collection_requests.find({'collector_id':ident}):
            h=db.households.find_one({'_id':job['household_id']})
            if not h or h['area'].casefold() not in [a.casefold() for a in doc['service_areas']]:
                raise ValueError('Keep service areas required by this collector’s existing requests.')
            if not active and job['status']!='completed':
                raise ValueError('Reassign or complete unfinished pickups before deactivating this collector.')
        doc['active']=active
    elif kind=='collection_requests':
        status=choice(data,'status',['pending','scheduled','completed'])
        if doc['household_id']!=old['household_id'] and db.payments.find_one({'request_id':ident}):
            raise ValueError('This request already has a billing record. Its household cannot be changed.')
        doc['status']=status
        doc['requested_at']=old['requested_at']
    elif kind=='payments':
        doc['paid_at']=(old.get('paid_at') or datetime.now(timezone.utc)) if doc['status']=='paid' else None
    result=db[kind].update_one({'_id':ident},{'$set':doc})
    if result.matched_count!=1: raise ValueError('Record no longer exists.')

def delete(kind,data):
    ident=text(data,'id')
    if kind=='households' and (db.collection_requests.find_one({'household_id':ident}) or db.payments.find_one({'household_id':ident})):
        raise ValueError('Delete this household’s linked payments and pickup requests first.')
    if kind=='collectors' and db.collection_requests.find_one({'collector_id':ident}):
        raise ValueError('This collector has pickup requests. Reassign or delete those requests first.')
    if kind=='collection_requests' and db.payments.find_one({'request_id':ident}):
        raise ValueError('Delete this request’s billing record first.')
    result=db[kind].delete_one({'_id':ident})
    if result.deleted_count!=1: raise ValueError('Record no longer exists. Refresh the records.')

def update(kind, data):
    ident=text(data,'id')
    if kind == 'collection_requests':
        status=choice(data,'status',['scheduled','completed'])
        previous='pending' if status=='scheduled' else 'scheduled'
        result=db[kind].update_one({'_id':ident,'status':previous},{'$set':{'status':status}})
    elif kind == 'payments':
        result=db[kind].update_one({'_id':ident,'status':'unpaid'},{'$set':{'status':'paid','paid_at':datetime.now(timezone.utc)}})
    else: raise ValueError('This action is not supported.')
    if result.matched_count != 1: raise ValueError('Record changed or the requested status transition is not allowed. Refresh and try again.')

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, payload, mime='application/json'):
        body = payload.encode() if isinstance(payload,str) else json.dumps(payload,default=lambda v:v.isoformat() if isinstance(v,datetime) else str(v)).encode()
        self.send_response(code);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def valid_host(self): return self.headers.get('Host') in ['127.0.0.1:8765','localhost:8765']
    def do_GET(self):
        if not self.valid_host(): return self.reply(403,{'error':'Invalid host'})
        if self.path == '/': return self.reply(200,(ROOT/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN),'text/html')
        if self.path != '/api/data': return self.reply(404,{'error':'Not found'})
        try:
            client.admin.command('ping')
            result={name:list(db[name].find({}).sort('_id',1)) for name in COLLECTIONS}
            result['database']=DB_NAME
            return self.reply(200,result)
        except PyMongoError: return self.reply(503,{'error':'Cannot connect to MongoDB. Start MongoDB, confirm Compass connects to localhost:27017, then retry.'})
    def do_POST(self):
        if not self.valid_host() or self.headers.get('X-App-Token') != TOKEN: return self.reply(403,{'error':'Refresh the application before saving.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0 < size <= 16384: raise ValueError('Invalid request size.')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('Invalid form data.')
            parts=self.path.split('/')
            if len(parts)!=4 or parts[1]!='api' or parts[2] not in COLLECTIONS or parts[3] not in ['create','update','edit','delete']: return self.reply(404,{'error':'Not found'})
            with LOCK:
                {'create':create,'update':update,'edit':edit,'delete':delete}[parts[3]](parts[2],data)
            return self.reply(200,{'message':'Saved successfully'})
        except DuplicateKeyError: return self.reply(409,{'error':'This pickup request already has a billing record.'})
        except (ValueError,TypeError,KeyError) as e: return self.reply(400,{'error':str(e)})
        except PyMongoError: return self.reply(503,{'error':'Database operation failed. Check MongoDB and retry.'})
    def log_message(self,*args): pass

if __name__=='__main__':
    try:
        client.admin.command('ping')
        if not set(COLLECTIONS).issubset(db.list_collection_names()):
            raise RuntimeError('The project collections were not found. Check WASTE_DATABASE before starting.')
        db.payments.create_index('request_id',unique=True)
        db.collection_requests.create_index([('status',1),('requested_at',1)])
        db.collection_requests.create_index('household_id')
        server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
        print('Waste Collection is running at http://127.0.0.1:8765\nKeep this window open. Press Ctrl+C to stop.')
        threading.Timer(1,lambda:webbrowser.open('http://127.0.0.1:8765')).start()
        server.serve_forever()
    except Exception as e:
        print('Could not start the application:',e)
        sys.exit(1)
