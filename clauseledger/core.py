"""Local-first contract indexing and citation-first retrieval."""
from __future__ import annotations
import hashlib
import re
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass(frozen=True)
class Hit:
    document_id: str
    source: str
    passage_id: int
    text: str
    start: int
    end: int
    score: float

POLICIES = {
    'termination': r'\bterminat(?:e|ion|ed)\b',
    'indemnity': r'\bindemnif(?:y|ication)|\bindemnity\b',
    'liability_cap': r'\blimitation of liability\b|\bliability (?:shall not )?exceed\b',
    'governing_law': r'\bgoverning law\b|\bgoverned by the laws\b',
    'renewal': r'\bauto(?:matic(?:ally)?)?[- ]renew\b|\brenewal\b',
}

def chunks(text: str, max_chars: int = 520) -> list[tuple[int,int,str]]:
    """Deterministic sentence packing; offsets point back into the original document."""
    if not text.strip():
        return []
    sentences=list(re.finditer(r'[^.!?\n]+(?:[.!?]+|\n|$)',text))
    out=[]
    pos=0
    while pos<len(sentences):
        a=sentences[pos].start(); end=pos
        while end+1<len(sentences) and sentences[end+1].end()-a<=max_chars:
            end+=1
        stop=sentences[end].end()
        if stop-a>max_chars:
            # Long sentence: divide without losing offsets.
            for start in range(a,stop,max_chars):
                finish=min(start+max_chars,stop)
                out.append((start,finish,text[start:finish]))
            pos=end+1
        else:
            out.append((a,stop,text[a:stop]));pos=end+1
    return out

class Ledger:
    def __init__(self, database: str | Path=':memory:'):
        self.con=sqlite3.connect(str(database),check_same_thread=False)
        self.con.row_factory=sqlite3.Row
        self.con.executescript("""
           CREATE TABLE IF NOT EXISTS documents (
             id TEXT PRIMARY KEY, source TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
             content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
           CREATE TABLE IF NOT EXISTS passages (
             id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL REFERENCES documents(id),
             start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL, text TEXT NOT NULL);
           CREATE TABLE IF NOT EXISTS audit (
             request_id TEXT PRIMARY KEY, query TEXT NOT NULL, matches INTEGER NOT NULL,
             created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
    def ingest(self,source:str,content:str)->dict:
        if not source.strip() or not content.strip():
            raise ValueError('source and content must not be blank')
        digest=hashlib.sha256(content.encode('utf8')).hexdigest()
        existing=self.con.execute('SELECT id FROM documents WHERE sha256=?',(digest,)).fetchone()
        if existing: return {'document_id':existing['id'],'duplicate':True}
        docid=str(uuid.uuid4())
        with self.con:
            self.con.execute('INSERT INTO documents(id,source,sha256,content) VALUES(?,?,?,?)',
                             (docid,source,digest,content))
            self.con.executemany('INSERT INTO passages(document_id,start_offset,end_offset,text) VALUES(?,?,?,?)',
                                  [(docid,a,b,t) for a,b,t in chunks(content)])
        return {'document_id':docid,'duplicate':False}
    def search(self, query:str, limit:int=5)->list[Hit]:
        if not query.strip(): raise ValueError('query must not be blank')
        if not 1<=limit<=20: raise ValueError('limit must be 1..20')
        rows=self.con.execute("""SELECT p.id,p.document_id,p.start_offset,p.end_offset,p.text,d.source
                                 FROM passages p JOIN documents d ON d.id=p.document_id ORDER BY p.id""").fetchall()
        if not rows: return []
        texts=[r['text'] for r in rows]
        scores=[]
        for analyzer,ngram,weight in [('word',(1,2),.65),('char_wb',(3,5),.35)]:
            vectorizer=TfidfVectorizer(analyzer=analyzer,ngram_range=ngram,sublinear_tf=True)
            matrix=vectorizer.fit_transform(texts)
            q=vectorizer.transform([query])
            scores.append(cosine_similarity(q,matrix).ravel()*weight)
        total=scores[0]+scores[1]
        ordered=sorted(range(len(rows)),key=lambda i:(-float(total[i]),rows[i]['id']))
        hits=[Hit(rows[i]['document_id'],rows[i]['source'],rows[i]['id'],rows[i]['text'],
                  rows[i]['start_offset'],rows[i]['end_offset'],round(float(total[i]),5))
              for i in ordered if total[i]>0][:limit]
        with self.con:
            self.con.execute('INSERT INTO audit(request_id,query,matches) VALUES(?,?,?)',
                             (str(uuid.uuid4()),query,len(hits)))
        return hits
    def risk_inventory(self,docid:str)->list[dict]:
        row=self.con.execute('SELECT content FROM documents WHERE id=?',(docid,)).fetchone()
        if row is None: raise KeyError(docid)
        text=row['content']; output=[]
        for name,pattern in POLICIES.items():
            match=re.search(pattern,text,re.I)
            output.append({'category':name,'found':match is not None,
                           'excerpt':text[max(0,match.start()-65):min(len(text),match.end()+100)].strip() if match else None})
        return output
    def audits(self,limit:int=20)->list[dict]:
        return [dict(r) for r in self.con.execute('SELECT * FROM audit ORDER BY created_at DESC, rowid DESC LIMIT ?', (limit,))]
