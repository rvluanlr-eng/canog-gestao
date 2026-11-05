import os,sys,subprocess
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='L'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,ContractLegalDetails,SessionLocal,render_legal_preview,Contract,Customer,Device
 from sqlalchemy import select
 from pathlib import Path
 from fastapi.testclient import TestClient
 t=TestClient(app)
 a=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()
 h={'Authorization':'Bearer '+a['access_token']}
 def post(path,data):
  r=t.post(path,headers=h,json=data);assert r.status_code in (200,201),r.text;return r.json()['id']
 c=post('/customers',{'name':'Maria Cliente','cpf':'11122233344','address':'Rua Principal 10','phone':'24999999999','email':'cliente@example.test'})
 g=post('/customers',{'name':'Joao Fiador','cpf':'55566677788','address':'Rua Segunda 20','phone':'24988888888'})
 dev=post('/devices',{'model':'iPhone 13','imei':'123456789012345','cost_cents':180000,'capacity':'128GB','color':'Azul'})
 con=post('/contracts',{'customer_id':c,'guarantor_id':g,'device_id':dev,'installments_count':12,'installment_cents':26500,'entry_cents':87500,'first_due':'2026-12-10T12:00:00'})
 before=t.get('/contracts/'+con+'/legal-draft.pdf',headers=h);assert before.status_code==422,before.text
 fields={'customer_postal_code':'27323000','customer_marital_status':'solteira','customer_occupation':'comerciante','guarantor_postal_code':'27323001','activation_fee_cents':0,'contract_end_date':'2027-11-10','inspection_date':'2026-11-10','contract_date':'2026-11-10'}
 r=t.put('/contracts/'+con+'/legal-details',headers=h,json=fields);assert r.status_code==200,r.text
 r=t.get('/contracts/'+con+'/legal-readiness',headers=h);assert r.status_code==200,r.text
 assert not r.json()['missing_contract_data'],r.json()['missing_contract_data']
 r=t.get('/contracts/'+con+'/legal-draft.pdf',headers=h);assert r.status_code==200,(r.status_code,r.text[:300]);assert r.content[:4]==b'%PDF' and len(r.content)>10000
 with SessionLocal() as s:
  contract=s.get(Contract,con);customer=s.get(Customer,c);guarantor=s.get(Customer,g);device=s.get(Device,dev)
  details=s.get(ContractLegalDetails,con)
  raw=(Path(sys.argv[1])/'contract_template.txt').read_text()
  filled,missing=render_legal_preview(raw,contract,customer,guarantor,device,details)
  assert not missing,missing
  assert 'Maria Cliente' in filled and 'Joao Fiador' in filled and '2027' in filled
  assert '[[PAGE_BREAK]]' in filled and 'ANEXO I' in filled
  assert '{{' not in filled
 print('PASS: legal details saved, original text filled, Annex I retained and PDF generated')
'''
def test_legal_details_complete_pdf():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
