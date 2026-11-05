import os, subprocess, sys
from pathlib import Path

BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r"""
import os,sys,tempfile
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='C'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,contract_template_issues
 from fastapi.testclient import TestClient
 t=TestClient(app)
 auth=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()
 h={'Authorization':'Bearer '+auth['access_token']}
 c=t.post('/customers',headers=h,json={'name':'Customer','cpf':'11122233344'}).json()['id']
 dev=t.post('/devices',headers=h,json={'model':'iPhone','imei':'123456789012345','cost_cents':10000}).json()['id']
 con=t.post('/contracts',headers=h,json={'customer_id':c,'device_id':dev,'installments_count':2,'installment_cents':10000}).json()['id']
 r=t.get('/contracts/'+con+'/legal-readiness',headers=h)
 assert r.status_code==200,r.text
 assert r.json()['ready_for_signature'] is False
 assert len(r.json()['unresolved_tokens'])>0
 r=t.get('/contracts/'+con+'/legal-draft.pdf',headers=h)
 assert r.status_code==422,r.text
 assert 'Dados contratuais obrigatórios' in r.text
 assert contract_template_issues('Olá {{NOME}} e XXXXX')['ready_for_signature'] is False
 assert contract_template_issues('Texto final')['ready_for_signature'] is True
 print('PASS: explicit contract fields reported and incomplete PDF blocked')
"""

def test_contract_readiness():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=45)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
