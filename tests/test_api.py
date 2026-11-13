from fastapi.testclient import TestClient
from clauseledger.api import app

def test_http_workflow():
    c=TestClient(app)
    assert c.get('/health').json()['status']=='ok'
    r=c.post('/documents',json={'source':'test-contract','content':'The agreement is governed by the laws of England.'})
    assert r.status_code==201
    docid=r.json()['document_id']
    assert c.get('/search',params={'q':'governed laws'}).json()['hits']
    assert c.get(f'/documents/{docid}/signals').status_code==200
    assert c.get('/documents/nonexistent/signals').status_code==404
