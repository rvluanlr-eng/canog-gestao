import os, sys, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/test.db',JWT_SECRET='B'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
 import bootstrap
 from main import app
 from fastapi.testclient import TestClient
 t=TestClient(app)
 login=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'})
 assert login.status_code==200,login.text
 h={'Authorization':'Bearer '+login.json()['access_token']}
 payload={'price_cents':120000,'cost_cents':80000,'entry_cents':20000,'trade_in_cents':0,'count':10,'rate_pct':0}
 r=t.post('/simulate',headers=h,json=payload)
 assert r.status_code==200,r.text
 assert r.json()['installment_cents']==10000 and r.json()['total_cents']==120000
 assert r.json()['validated_against_original'] is False
 payload['rate_pct']=8
 r=t.post('/simulate',headers=h,json=payload)
 assert r.status_code==200 and r.json()['installment_cents']>10000,r.text
 payload['entry_cents']=120001
 assert t.post('/simulate',headers=h,json=payload).status_code==422
 print('PASS: zero-rate, Price, validation, explicit provisional flag')
