import os, subprocess, sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
from datetime import datetime,timedelta,timezone
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='T'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,SessionLocal,Contract,Installment
 from fastapi.testclient import TestClient
 t=TestClient(app)
 auth=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()
 h={'Authorization':'Bearer '+auth['access_token']}
 customer=t.post('/customers',headers=h,json={'name':'Test Customer','cpf':'22233344455'}).json()['id']
 device=t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':90000}).json()['id']
 cid=t.post('/contracts',headers=h,json={'customer_id':customer,'device_id':device,'installments_count':2,'installment_cents':60000}).json()['id']
 with SessionLocal() as s:
  c=s.get(Contract,cid)
  p=Installment(tenant_id=c.tenant_id,contract_id=cid,number=1,amount_cents=60000,due_at=datetime.now(timezone.utc)-timedelta(days=3))
  s.add(p);s.commit();pid=p.id
 r=t.post('/installments/'+pid+'/confirm',headers=h)
 assert r.status_code==409,r.text
 report=t.get('/reports/financial',headers=h).json()
 assert report['receivable_cents']==0,report
 assert report['overdue_cents']==0,report
 readiness=t.get('/admin/deployment-readiness',headers=h).json()
 assert readiness['configuration_ready'] is False,readiness
 assert readiness['legal_template_ready'] is False,readiness
 print('PASS: draft payment rejected, draft excluded from receivables, legal blockers reported')
'''
def test_release_guards():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
