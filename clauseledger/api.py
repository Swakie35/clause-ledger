from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from .core import Ledger

app=FastAPI(title='ClauseLedger',version='0.1.0',description='Evidence-first contract search demo')
ledger=Ledger('clauseledger.sqlite')

class Document(BaseModel):
    source: str=Field(min_length=1,max_length=200)
    content: str=Field(min_length=1,max_length=100000)

@app.get('/health')
def health(): return {'status':'ok'}

@app.post('/documents',status_code=201)
def add_document(document:Document):
    return ledger.ingest(document.source,document.content)

@app.get('/search')
def search(q:str=Query(min_length=1),limit:int=Query(5,ge=1,le=20)):
    return {'query':q,'hits':[asdict(hit) for hit in ledger.search(q,limit)],'note':'Scores are lexical relevance, not legal certainty.'}

@app.get('/documents/{document_id}/signals')
def signals(document_id:str):
    try: return {'document_id':document_id,'signals':ledger.risk_inventory(document_id)}
    except KeyError: raise HTTPException(status_code=404,detail='Document not found')

@app.get('/audit')
def audit(): return {'events':ledger.audits()}
