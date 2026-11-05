import os,sys,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/test.db',JWT_SECRET='A'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
 import bootstrap
 from main import app
 from fastapi.testclient import TestClient
 t=TestClient(app)
 def ok(r):
  assert r.status_code in (200,201),(r.status_code,r.text)
  return r.json()
 a=ok(t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}))
 h={'Authorization':'Bearer '+a['access_token']}
 c=ok(t.post('/customers',headers=h,json={'name':'Maria Teste','cpf':'12345678901'}))['id']
 g=ok(t.post('/customers',headers=h,json={'name':'Fiador Teste','cpf':'12345678902'}))['id']
 dev=ok(t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':180000}))['id']
 con=ok(t.post('/contracts',headers=h,json={'customer_id':c,'guarantor_id':g,'device_id':dev,'installments_count':12,'installment_cents':20000,'first_due':'2026-12-10T12:00:00'}))['id']
 r=t.post('/contracts/'+con+'/activate',headers=h);assert r.status_code==409,r.text
 r=t.get('/contracts/'+con+'/legal-draft.pdf',headers=h);assert r.status_code==422 and 'Dados contratuais obrigatórios' in r.text,(r.status_code,r.text[:100])
 ok(t.post('/portal/access',headers=h,json={'customer_id':c,'password':'SomeOtherStrongPassword'}))
 pt=ok(t.post('/portal/login',json={'cpf':'12345678901','password':'SomeOtherStrongPassword','tenant_id':__import__('jwt').decode(a['access_token'],'A'*48,algorithms=['HS256'],options={'verify_aud':False})['tenant']}))['access_token']
 assert t.get('/customers',headers={'Authorization':'Bearer '+pt}).status_code==401,'portal token admin escalation'
 print('PASS: login, cadastro, rascunho, bloqueio, bloqueio de minuta incompleta, portal e isolamento de token')
