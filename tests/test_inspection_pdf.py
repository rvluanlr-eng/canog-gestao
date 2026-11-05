import subprocess,sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile,io
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='I'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app,INSPECTION_FIELDS
 from fastapi.testclient import TestClient
 from pypdf import PdfReader
 t=TestClient(app)
 token=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()['access_token']
 h={'Authorization':'Bearer '+token}
 def post(path,body):
  r=t.post(path,headers=h,json=body);assert r.status_code in (200,201),r.text;return r.json()['id']
 customer=post('/customers',{'name':'Cliente Teste','cpf':'11122233344'})
 device=post('/devices',{'model':'iPhone 13','imei':'123456789012345','cost_cents':100000})
 cid=post('/contracts',{'customer_id':customer,'device_id':device,'installments_count':12,'installment_cents':20000})
 url='/contracts/'+cid+'/review-copy.pdf'
 r=t.get(url,headers=h);assert r.status_code==200,r.text
 text=' '.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(r.content)).pages)
 assert 'VISTORIA DIGITAL NÃO REGISTRADA' in text
 checks={key:'ok' for key in INSPECTION_FIELDS};checks['battery']='issue'
 r=t.put('/contracts/'+cid+'/inspection',headers=h,json={'checks':checks,'observations':'Bateria com desgaste','accessories':'Carregador'});assert r.status_code==200,r.text
 r=t.get(url,headers=h);assert r.status_code==200,r.text
 pdf=PdfReader(io.BytesIO(r.content));text=' '.join((p.extract_text() or '') for p in pdf.pages)
 assert 'RELATÓRIO COMPLEMENTAR DA VISTORIA DIGITAL' in text
 assert 'Bateria: Com ressalva' in text
 assert 'Bateria com desgaste' in text
 assert 'Carregador' in text
 assert 'ANEXO I' in text
 assert t.get(url).status_code==401
 print('PASS: digital inspection appears in review PDF and original annex remains')
'''
def test_inspection_pdf():
 p=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert p.returncode==0,p.stdout+'\n'+p.stderr
