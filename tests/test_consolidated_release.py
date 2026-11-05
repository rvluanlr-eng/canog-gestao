"""Financial recovery, active-only dashboard and fail-closed production guards."""
import subprocess, sys
from pathlib import Path

BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
from datetime import datetime,timedelta,timezone
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='Z'*48,PRIVATE_STORAGE=d+'/files',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='StrongPassword_123456')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,SessionLocal,Contract,Installment,production_configuration_errors
 from fastapi.testclient import TestClient
 t=TestClient(app)
 token=t.post('/auth/login',json={'email':'admin@example.test','password':'StrongPassword_123456'}).json()['access_token']
 h={'Authorization':'Bearer '+token}
 c=t.post('/customers',headers=h,json={'name':'Cliente Teste','cpf':'55566677788'}).json()['id']
 dev=t.post('/devices',headers=h,json={'model':'iPhone 14','imei':'123456789012345','cost_cents':100000}).json()['id']
 cid=t.post('/contracts',headers=h,json={'customer_id':c,'device_id':dev,'installments_count':2,'installment_cents':80000}).json()['id']
 with SessionLocal() as s:
  contract=s.get(Contract,cid)
  contract.status='active'
  p=Installment(tenant_id=contract.tenant_id,contract_id=cid,number=1,amount_cents=80000,due_at=datetime.now(timezone.utc)-timedelta(days=3),status='paid')
  p2=Installment(tenant_id=contract.tenant_id,contract_id=cid,number=2,amount_cents=80000,due_at=datetime.now(timezone.utc)-timedelta(days=1),status='pending')
  s.add_all([p,p2]);s.flush();p2_id=p2.id;s.commit()
 r=t.get('/reports/cost-recovery',headers=h)
 assert r.status_code==200,r.text
 x=r.json()['contracts'][0]
 assert x['confirmed_installments_cents']==80000 and x['cost_recovered_cents']==80000 and x['realized_profit_cents']==0,x
 dash=t.get('/dashboard',headers=h).json()
 assert dash['outstanding_cents']==80000 and dash['overdue_count']==1,dash
 with SessionLocal() as s:
  p=s.get(Installment,p2_id);p.status='paid';s.commit()
 x=t.get('/reports/cost-recovery',headers=h).json()['contracts'][0]
 assert x['realized_profit_cents']==60000 and x['partner_share_cents']==12000,x
 assert x['company_profit_cents']==48000,x
 os.environ['APP_ENV']='production'
 assert production_configuration_errors(), 'production should fail closed without postgres/R2/HTTPS'
 print('PASS: recovery, partner share, dashboard and production guard')
'''

def test_consolidated_release():
 result=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=80)
 assert result.returncode==0,result.stdout+'\n'+result.stderr
