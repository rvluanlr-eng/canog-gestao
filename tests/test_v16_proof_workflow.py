"""Payment proof approval/rejection must be explicit and audited."""
import subprocess,sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile,io
from datetime import datetime,timedelta,timezone
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(DATABASE_URL='sqlite:///'+tmp+'/db.sqlite',JWT_SECRET='T'*48,PRIVATE_STORAGE=tmp+'/private',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,SessionLocal,Installment,Document,Audit,Contract,Customer
 from fastapi.testclient import TestClient
 t=TestClient(app)
 h={'Authorization':'Bearer '+t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()['access_token']}
 cust=t.post('/customers',headers=h,json={'name':'Cliente','cpf':'12345678901'}).json()['id']
 device=t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':10000}).json()['id']
 cid=t.post('/contracts',headers=h,json={'customer_id':cust,'device_id':device,'installments_count':1,'installment_cents':10000}).json()['id']
 with SessionLocal() as s:
  contract=s.get(Contract,cid);contract.status='active'
  p=Installment(tenant_id=contract.tenant_id,contract_id=cid,number=1,amount_cents=10000,due_at=datetime.now(timezone.utc)+timedelta(days=5),status='review')
  proof=Document(tenant_id=contract.tenant_id,contract_id=cid,kind='pix_proof',filename='proof.pdf',path='test',mime='application/pdf',uploaded_by=cust)
  s.add_all([p,proof]);s.flush();p.proof_id=proof.id;pid=p.id;did=proof.id;s.commit()
 assert t.post('/installments/'+pid+'/confirm',headers=h).status_code==409
 assert t.post('/installments/'+pid+'/approve-proof').status_code==401
 r=t.post('/installments/'+pid+'/approve-proof',headers=h)
 assert r.status_code==200,r.text
 assert t.post('/installments/'+pid+'/approve-proof',headers=h).status_code==409
 with SessionLocal() as s:
  p=s.get(Installment,pid);proof=s.get(Document,did)
  assert p.status=='paid' and p.confirmed_by and p.paid_at and proof.status=='approved'
  assert any(a.action=='installment.proof_approved' and a.target_id==pid for a in s.query(Audit).all())
  p.status='review';p.paid_at=None;p.confirmed_by=None
  proof.status='pending';s.commit()
 r=t.post('/installments/'+pid+'/reject-proof',headers=h,json={'reason':'Comprovante não corresponde ao valor'})
 assert r.status_code==200,r.text
 with SessionLocal() as s:
  assert s.get(Installment,pid).status=='pending' and s.get(Installment,pid).proof_id is None
  assert s.get(Document,did).status=='rejected'
 print('PASS: proof approval, rejection, access and audit')
'''
def test_v16_proof_workflow():
 p=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert p.returncode==0,p.stdout+'\n'+p.stderr
