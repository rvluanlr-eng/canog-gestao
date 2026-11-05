import os,sys,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/test.db',JWT_SECRET='Z'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
 import bootstrap
 from main import app
 from fastapi.testclient import TestClient
 t=TestClient(app)
 def ok(r,code=200):
  assert r.status_code==code,(r.status_code,r.text)
  return r.json()
 h={'Authorization':'Bearer '+ok(t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}))['access_token']}
 c=ok(t.post('/customers',headers=h,json={'name':'Cliente','cpf':'12345678901'}),201)['id']
 g=ok(t.post('/customers',headers=h,json={'name':'Fiador','cpf':'12345678902'}),201)['id']
 d1=ok(t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':200000}),201)['id']
 contract=ok(t.post('/contracts',headers=h,json={'customer_id':c,'guarantor_id':g,'device_id':d1,'installments_count':2,'installment_cents':10000,'trade_in_cents':50000,'first_due':'2026-12-10T12:00:00'}),201)['id']
 assert t.post(f'/contracts/{contract}/activate',headers=h).status_code==409
 ti=ok(t.post(f'/contracts/{contract}/trade-in',headers=h,json={'model':'iPhone 8','imei':'123456789012346','cost_cents':50000}),201)
 assert ti['allowance_cents']==50000
 assert t.post(f'/contracts/{contract}/trade-in',headers=h,json={'model':'iPhone 8','imei':'123456789012347','cost_cents':50000}).status_code==409
 check=ok(t.get(f'/contracts/{contract}/checklist',headers=h))
 assert len(check['missing_documents'])==8
 assert t.post(f'/contracts/{contract}/close',headers=h,json={'action':'acquire','residual_paid':True,'transfer_signed':True}).status_code==409
 assert len(ok(t.get('/audit',headers=h)))>=4
 print('PASS: trade-in inventory, duplicate protection, checklist, lifecycle guards, audit')
