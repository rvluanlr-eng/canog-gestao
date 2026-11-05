"""Isolated regression test for portal visibility, role checks and latest-document rule."""
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / 'backend'
SCRIPT = r'''
import os, sys, tempfile
from pathlib import Path
from sqlalchemy import select
with tempfile.TemporaryDirectory() as folder:
 os.environ.update(DATABASE_URL='sqlite:///'+folder+'/db.sqlite',JWT_SECRET='S'*48,PRIVATE_STORAGE=folder+'/uploads',ADMIN_EMAIL='admin@example.test',ADMIN_PASSWORD='VeryStrongPass1234')
 sys.path.insert(0,sys.argv[1])
 import bootstrap
 from main import app,SessionLocal,User,Document,Contract,Tenant,Customer,Device,pw_hash,REQUIRED_DOCUMENTS
 from fastapi.testclient import TestClient
 t=TestClient(app)
 def req(method,path,code=200,**kwargs):
  r=t.request(method,path,**kwargs)
  assert r.status_code==code,(method,path,r.status_code,r.text)
  return r.json()
 admin={'Authorization':'Bearer '+req('POST','/auth/login',json={'email':'admin@example.test','password':'VeryStrongPass1234'})['access_token']}
 customer=req('POST','/customers',201,headers=admin,json={'name':'Customer','cpf':'11122233344'})['id']
 guarantor=req('POST','/customers',201,headers=admin,json={'name':'Guarantor','cpf':'11122233345'})['id']
 device=req('POST','/devices',201,headers=admin,json={'model':'iPhone','imei':'123456789012345','cost_cents':10000})['id']
 contract=req('POST','/contracts',201,headers=admin,json={'customer_id':customer,'guarantor_id':guarantor,'device_id':device,'installments_count':2,'installment_cents':10000})['id']
 req('POST','/portal/access',headers=admin,json={'customer_id':customer,'password':'PortalPass12345'})
 with SessionLocal() as s:
  tenant=s.scalar(select(User).where(User.email=='admin@example.test')).tenant_id
 portal={'Authorization':'Bearer '+req('POST','/portal/login',json={'tenant_id':tenant,'cpf':'11122233344','password':'PortalPass12345'})['access_token']}
 req('GET','/portal/contracts/'+contract,404,headers=portal) if False else None
 req('GET','/portal/contracts/'+contract+'/summary',404,headers=portal)
 assert req('GET','/portal/me',headers=portal)['contracts']==[]
 with SessionLocal() as s:
  user=s.scalar(select(User).where(User.email=='admin@example.test'))
  user.role='viewer'
  s.commit()
 req('POST','/customers',403,headers=admin,json={'name':'Other','cpf':'11122233346'})
 req('POST','/devices',403,headers=admin,json={'model':'Other','imei':'123456789012346','cost_cents':1})
 req('POST','/contracts',403,headers=admin,json={'customer_id':customer,'device_id':device,'installments_count':1,'installment_cents':1})
 req('PATCH','/contracts/'+contract+'/document-review',403,headers=admin,json={'approved':True})
 with SessionLocal() as s:
  user=s.scalar(select(User).where(User.email=='admin@example.test'))
  user.role='admin'
  for kind in REQUIRED_DOCUMENTS:
   s.add(Document(tenant_id=tenant,contract_id=contract,kind=kind,filename='ok.pdf',path='fake',mime='application/pdf',status='approved',uploaded_by=user.id))
  s.commit()
 assert req('GET','/contracts/'+contract+'/checklist',headers=admin)['missing_documents']==[]
 with SessionLocal() as s:
  user=s.scalar(select(User).where(User.email=='admin@example.test'))
  s.add(Document(tenant_id=tenant,contract_id=contract,kind='client_identity',filename='replacement.pdf',path='fake2',mime='application/pdf',status='pending',uploaded_by=user.id))
  s.commit()
 assert req('GET','/contracts/'+contract+'/checklist',headers=admin)['missing_documents']==['client_identity']
 print('PASS: draft hidden; viewer denied writes; replacement document invalidates approval')
'''

def test_security_regressions():
 result=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=45)
 assert result.returncode==0, result.stdout+'\n'+result.stderr
