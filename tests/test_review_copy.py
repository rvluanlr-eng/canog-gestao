import subprocess,sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='C'*48,PRIVATE_STORAGE=d+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1]);import bootstrap
 from main import app
 from fastapi.testclient import TestClient
 t=TestClient(app)
 auth=t.post('/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'}).json()
 h={'Authorization':'Bearer '+auth['access_token']}
 c=t.post('/customers',headers=h,json={'name':'Maria Teste','cpf':'11122233344','phone':'24999999999','address':'Rua Exemplo, 10'}).json()['id']
 g=t.post('/customers',headers=h,json={'name':'Fiador Teste','cpf':'22233344455','phone':'24988888888','address':'Rua Teste, 20'}).json()['id']
 dev=t.post('/devices',headers=h,json={'model':'iPhone 13','imei':'123456789012345','cost_cents':10000,'color':'Preto','capacity':'128 GB'}).json()['id']
 con=t.post('/contracts',headers=h,json={'customer_id':c,'guarantor_id':g,'device_id':dev,'installments_count':2,'installment_cents':10000,'first_due':'2026-12-10T00:00:00'}).json()['id']
 r=t.get('/contracts/'+con+'/review-copy.pdf',headers=h)
 assert r.status_code==200,r.text
 assert r.content.startswith(b'%PDF')
 assert len(r.content)>10000
 assert r.headers['cache-control']=='no-store'
 from pypdf import PdfReader
 import io
 pdf=PdfReader(io.BytesIO(r.content))
 content=' '.join(page.extract_text() or '' for page in pdf.pages)
 assert 'Maria Teste' in content
 assert 'Fiador Teste' in content
 assert 'NÃO ASSINAR' in content
 assert 'PENDENTE' in content
 assert 'ANEXO I' in content
 assert len(pdf.pages)>=16,len(pdf.pages)
 print('PASS:',len(pdf.pages),'pages; pending fields visibly marked')
'''
def test_review_copy():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
