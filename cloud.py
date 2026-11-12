"""Hosted entry point. Run behind HTTPS with gunicorn cloud:application."""
import os, secrets, hmac
from datetime import datetime
from flask import Flask, request, jsonify, Response
from pymongo.errors import DuplicateKeyError, PyMongoError
import app as core

if not os.getenv('MONGODB_URI'):
    raise RuntimeError('Set MONGODB_URI to the online database connection string.')
PASSWORD=os.environ.get('APP_PASSWORD','')
USERNAME=os.environ.get('APP_USERNAME','lecturer')
if len(PASSWORD)<16:
    raise RuntimeError('Set APP_PASSWORD to a unique password of at least 16 characters.')
application=Flask(__name__)
application.config['MAX_CONTENT_LENGTH']=16384
application.json.default=lambda value: value.isoformat() if isinstance(value,datetime) else str(value)

@application.before_request
def protect():
    if request.path=='/healthz': return None
    auth=request.authorization
    if not auth or not hmac.compare_digest(auth.username or '',USERNAME) or not hmac.compare_digest(auth.password or '',PASSWORD):
        return Response('Sign in to view the community waste collection project.',401,{'WWW-Authenticate':'Basic realm="Waste Collection Project", charset="UTF-8"'})

@application.after_request
def headers(response):
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    return response

@application.get('/healthz')
def health():
    try:
        core.client.admin.command('ping')
        return jsonify(status='ok')
    except PyMongoError: return jsonify(status='unavailable'),503

@application.get('/')
def home():
    return Response((core.ROOT/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',core.TOKEN),mimetype='text/html')

@application.get('/api/data')
def data():
    try:
        result={name:list(core.db[name].find({}).sort('_id',1)) for name in core.COLLECTIONS}
        result['database']=core.DB_NAME
        return jsonify(result)
    except PyMongoError: return jsonify(error='Online database unavailable. Contact the project owner.'),503

@application.post('/api/<kind>/<action>')
def save(kind,action):
    if not hmac.compare_digest(request.headers.get('X-App-Token',''),core.TOKEN):
        return jsonify(error='Refresh the application before saving.'),403
    if kind not in core.COLLECTIONS or action not in ['create','update','edit','delete']:
        return jsonify(error='Not found'),404
    data=request.get_json(silent=True)
    if not isinstance(data,dict):return jsonify(error='Invalid form data.'),400
    try:
        with core.LOCK:
            {'create':core.create,'update':core.update,'edit':core.edit,'delete':core.delete}[action](kind,data)
        return jsonify(message='Saved successfully')
    except DuplicateKeyError:return jsonify(error='This pickup request already has a billing record.'),409
    except (ValueError,KeyError,TypeError) as e:return jsonify(error=str(e)),400
    except PyMongoError:return jsonify(error='Database operation failed. Please retry.'),503
