"""Standalone API regression test for due alerts and closed-contract proof protection."""
import os, subprocess, sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
from datetime import datetime,timedelta,timezone
from sqlalchemy import select
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(DATABASE_URL='sqlite:///'+tmp+'/db.sqlite',JWT_SECRET='Z'*48,PRIVATE_STORAGE=tmp+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,SessionLocal,User,Contract,Installment,Customer
 from fastapi.testclient import TestClient
 t=TestClient(app)
 token=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()['access_token']
 h={'Authorization':'Bearer '+token}
 today=datetime.now(timezone.utc).date()
 with SessionLocal() as s:
  u=s.scalar(select(User).where(User.email=='admin@example.test'))
  c=Customer(tenant_id=u.tenant_id,name='Cliente',cpf='11122233344')
  s.add(c);s.flush()
  active=Contract(tenant_id=u.tenant_id,customer_id=c.id,device_id='fake',status='active')
  closed=Contract(tenant_id=u.tenant_id,customer_id=c.id,device_id='fake2',status='returned')
  s.add_all([active,closed]);s.flush()
  for contract,offset,status,amount in [(active,3,'pending',5000),(active,-2,'review',7000),(active,9,'pending',9000),(active,1,'paid',1000),(closed,1,'pending',8000)]:
   s.add(Installment(tenant_id=u.tenant_id,contract_id=contract.id,number=1,amount_cents=amount,due_at=datetime.combine(today+timedelta(days=offset),datetime.min.time()),status=status))
  active_id=active.id;closed_id=closed.id;customer_id=c.id;tenant=u.tenant_id
  s.commit()
 r=t.get('/reports/upcoming-due?days=7',headers=h)
 assert r.status_code==200,r.text
 data=r.json();assert data['upcoming_total_cents']==5000,data
 assert data['overdue_total_cents']==7000,data
 assert len(data['upcoming'])==len(data['overdue'])==1,data
 assert t.get('/reports/upcoming-due?days=32',headers=h).status_code==422
 assert t.get('/reports/upcoming-due').status_code==401
 assert t.post('/portal/access',headers=h,json={'customer_id':customer_id,'password':'StrongPortalPass123'}).status_code==200
 portal=t.post('/portal/login',json={'tenant_id':tenant,'cpf':'11122233344','password':'StrongPortalPass123'}).json()['access_token']
 with SessionLocal() as s:
  closed_inst=s.scalar(select(Installment).where(Installment.contract_id==closed_id))
  installment_id=closed_inst.id
 resp=t.post('/portal/installments/'+installment_id+'/proof',headers={'Authorization':'Bearer '+portal},files={'file':('proof.pdf',b'%PDF-1.4\nhello','application/pdf')})
 assert resp.status_code==409,resp.text
 print('PASS: due alerts, tenant scope, closed-contract upload blocked')
'''
def test_v12_due_alerts():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
