from clauseledger.core import Ledger,chunks

def test_offsets_are_exact():
    text='Hello world. Governing law is England! Renew annually.'
    assert all(text[a:b]==part for a,b,part in chunks(text))

def test_duplicate_and_retrieval():
    l=Ledger()
    doc=l.ingest('nda.txt','The governing law is England. Either party may terminate with notice.')
    assert l.ingest('same.txt','The governing law is England. Either party may terminate with notice.')['duplicate']
    hits=l.search('governing law england')
    assert hits and hits[0].document_id==doc['document_id']
    assert hits[0].score>0
    assert l.audits()[0]['matches']>0

def test_risk_inventory():
    l=Ledger(); d=l.ingest('a','This contract has automatic renewal.')
    signals={x['category']:x['found'] for x in l.risk_inventory(d['document_id'])}
    assert signals['renewal'] and not signals['indemnity']

def test_missing_and_empty():
    l=Ledger()
    assert l.search('none')==[]
    try:l.ingest('','hello')
    except ValueError:pass
    else:raise AssertionError('Expected validation error')
