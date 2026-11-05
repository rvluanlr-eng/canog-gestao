"""Configuration and legal data regressions isolated in a subprocess database."""
import subprocess,sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(DATABASE_URL='sqlite:///'+tmp+'/db.sqlite',JWT_SECRET='T'*48,PRIVATE_STORAGE=tmp+'/private',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app
 from fastapi.testclient import TestClient
 t=TestClient(app)
 h={'Authorization':'Bearer '+t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()['access_token']}
 assert t.get('/admin/deployment-readiness').status_code==401
 status=t.get('/admin/deployment-readiness',headers=h)
 assert status.status_code==200,status.text
 data=status.json();assert data['checks']['jwt_secret_configured']
 assert not data['checks']['database_postgresql']
 assert not data['configuration_ready']
 cust=t.post('/customers',headers=h,json={'name':'Cliente','cpf':'12345678901'}).json()['id']
 device=t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':10000}).json()['id']
 contract=t.post('/contracts',headers=h,json={'customer_id':cust,'device_id':device,'installments_count':12,'installment_cents':10000}).json()['id']
 r=t.get('/contracts/'+contract+'/legal-readiness',headers=h)
 assert 'customer.address' in r.json()['missing_contract_data']
 assert 'guarantor' in r.json()['missing_contract_data']
 pdf=t.get('/contracts/'+contract+'/legal-draft.pdf',headers=h)
 assert pdf.status_code==422,pdf.text
 assert 'customer.address' in pdf.json()['detail']['missing_contract_data']
 print('PASS: deployment preflight and legal-data gating')
'''
def test_v15_readiness():
 p=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert p.returncode==0,p.stdout+'\n'+p.stderr
