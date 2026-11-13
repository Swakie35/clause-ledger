"""A tiny, repeatable retrieval benchmark with a human-readable evidence target."""
from __future__ import annotations
from .core import Ledger

def benchmark()->dict:
    documents={
        'supplier-terms':'The supplier shall deliver the goods within fifteen business days after receipt of the purchase order. Freight is paid by the supplier.',
        'services-agreement':'This services agreement includes automatic renewal for annual terms. Either party may terminate with sixty days written notice.',
        'nda':'Confidential information may not be disclosed except to authorised personnel. The governing law is England and Wales.',
    }
    questions=[('How quickly are the goods delivered?','supplier-terms'),
               ('Is this contract automatically renewed?','services-agreement'),
               ('What law governs the NDA?','nda')]
    ledger=Ledger()
    ids={source:ledger.ingest(source,text)['document_id'] for source,text in documents.items()}
    reciprocal=[]
    for query,expected in questions:
        hits=ledger.search(query,limit=5)
        rank=next((i+1 for i,hit in enumerate(hits) if hit.document_id==ids[expected]),None)
        reciprocal.append(0 if rank is None else 1/rank)
    return {'dataset':'three short, invented test contracts',
            'queries':len(questions),'mean_reciprocal_rank_at_5':round(sum(reciprocal)/len(reciprocal),4)}

if __name__=='__main__':print(benchmark())
