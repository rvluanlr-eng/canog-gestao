import subprocess, sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='I'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,INSPECTION_FIELDS
 from fastapi.testclient import TestClient
 t=TestClient(app)
 token=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()['access_token']
 h={'Authorization':'Bearer '+token}
 def post(path,body):
  r=t.post(path,headers=h,json=body);assert r.status_code in (200,201),r.text;return r.json()['id']
 customer=post('/customers',{'name':'Teste Cliente','cpf':'11122233344'})
 device=post('/devices',{'model':'iPhone 13','imei':'123456789012345','cost_cents':100000})
 cid=post('/contracts',{'customer_id':customer,'device_id':device,'installments_count':12,'installment_cents':20000})
 url='/contracts/'+cid+'/inspection'
 assert t.get(url,headers=h).json()['completed'] is False
 assert t.get('/contracts/'+cid+'/checklist',headers=h).json()['inspection_completed'] is False
 assert t.put(url,headers=h,json={'checks':{'screen':'ok'}}).status_code==422
 checks={key:'ok' for key in INSPECTION_FIELDS}
 checks['battery']='issue'
 assert t.put(url,headers=h,json={'checks':checks}).status_code==422
 r=t.put(url,headers=h,json={'checks':checks,'observations':'Bateria com desgaste','accessories':'Carregador'});assert r.status_code==200,r.text
 r=t.get(url,headers=h);assert r.status_code==200 and r.json()['completed'] and r.json()['checks']['battery']=='issue'
 assert t.get('/contracts/'+cid+'/checklist',headers=h).json()['inspection_completed'] is True
 assert t.get(url).status_code==401
 print('PASS: inspection validation, persistence, checklist and authorization')
'''
def test_inspection_flow():
 p=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert p.returncode==0,p.stdout+'\n'+p.stderr
