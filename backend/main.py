"""CANOG Gestão: API foundation. Not yet production-ready."""
import os, uuid, hashlib, hmac, secrets, io, calendar, re, base64, mimetypes, pathlib, json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone, date
from typing import Optional
import jwt
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Integer, ForeignKey, DateTime, Numeric, Boolean, select, UniqueConstraint, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./canog_dev.db')
if DATABASE_URL.startswith('postgres://'): DATABASE_URL='postgresql://'+DATABASE_URL[11:]
engine=create_engine(DATABASE_URL, connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine)
SECRET=os.getenv('JWT_SECRET','')
app=FastAPI(title='CANOG Gestão API',version='0.18.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()],allow_methods=['GET','POST','PATCH','PUT'],allow_headers=['Authorization','Content-Type'])
class Base(DeclarativeBase): pass
class Tenant(Base):
 __tablename__='tenants'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 name:Mapped[str]=mapped_column(String(160))
class User(Base):
 __tablename__='users'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 email:Mapped[str]=mapped_column(String(200),unique=True)
 password_hash:Mapped[str]=mapped_column(String(250))
 role:Mapped[str]=mapped_column(String(30),default='admin')
class Customer(Base):
 __tablename__='customers'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 name:Mapped[str]=mapped_column(String(160))
 cpf:Mapped[str]=mapped_column(String(11))
 phone:Mapped[str]=mapped_column(String(30),default='')
 email:Mapped[str]=mapped_column(String(200),default='')
 address:Mapped[str]=mapped_column(String(500),default='')
 __table_args__=(UniqueConstraint('tenant_id','cpf'),)
class Device(Base):
 __tablename__='devices'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 model:Mapped[str]=mapped_column(String(120))
 imei:Mapped[str]=mapped_column(String(20))
 cost_cents:Mapped[int]=mapped_column(Integer)
 color:Mapped[str]=mapped_column(String(60),default='')
 capacity:Mapped[str]=mapped_column(String(60),default='')
 status:Mapped[str]=mapped_column(String(25),default='available')
 __table_args__=(UniqueConstraint('tenant_id','imei'),)
class Contract(Base):
 __tablename__='contracts'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 customer_id:Mapped[str]=mapped_column(String(36))
 guarantor_id:Mapped[Optional[str]]=mapped_column(String(36),nullable=True)
 device_id:Mapped[str]=mapped_column(String(36))
 status:Mapped[str]=mapped_column(String(25),default='draft')
 documents_approved:Mapped[bool]=mapped_column(Boolean,default=False)
 installments_count:Mapped[int]=mapped_column(Integer,default=12)
 installment_cents:Mapped[int]=mapped_column(Integer,default=0)
 entry_cents:Mapped[int]=mapped_column(Integer,default=0)
 trade_in_cents:Mapped[int]=mapped_column(Integer,default=0)
 residual_cents:Mapped[int]=mapped_column(Integer,default=0)
 first_due:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
 signed_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
 delivered_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class Installment(Base):
 __tablename__='installments'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 contract_id:Mapped[str]=mapped_column(String(36),index=True)
 number:Mapped[int]=mapped_column(Integer)
 amount_cents:Mapped[int]=mapped_column(Integer)
 due_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
 status:Mapped[str]=mapped_column(String(25),default='pending')
 paid_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
 confirmed_by:Mapped[Optional[str]]=mapped_column(String(36),nullable=True)
 proof_id:Mapped[Optional[str]]=mapped_column(String(36),nullable=True)
class Audit(Base):
 __tablename__='audit_logs'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(String(36),index=True)
 actor_id:Mapped[str]=mapped_column(String(36))
 action:Mapped[str]=mapped_column(String(80))
 target_id:Mapped[str]=mapped_column(String(36))
 at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Document(Base):
 __tablename__='documents'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 contract_id:Mapped[str]=mapped_column(String(36),index=True)
 kind:Mapped[str]=mapped_column(String(40))
 filename:Mapped[str]=mapped_column(String(200))
 path:Mapped[str]=mapped_column(String(500))
 mime:Mapped[str]=mapped_column(String(100))
 status:Mapped[str]=mapped_column(String(20),default='pending')
 uploaded_by:Mapped[str]=mapped_column(String(36))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class ContractLegalDetails(Base):
 __tablename__='contract_legal_details'
 contract_id:Mapped[str]=mapped_column(String(36),primary_key=True)
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 customer_postal_code:Mapped[str]=mapped_column(String(20),default='')
 customer_marital_status:Mapped[str]=mapped_column(String(80),default='')
 customer_occupation:Mapped[str]=mapped_column(String(120),default='')
 guarantor_postal_code:Mapped[str]=mapped_column(String(20),default='')
 activation_fee_cents:Mapped[Optional[int]]=mapped_column(Integer,nullable=True)
 contract_end_date:Mapped[Optional[date]]=mapped_column(nullable=True)
 inspection_date:Mapped[Optional[date]]=mapped_column(nullable=True)
 contract_date:Mapped[Optional[date]]=mapped_column(nullable=True)

class LegalDetailsIn(BaseModel):
 customer_postal_code:str=Field(min_length=8,max_length=20)
 customer_marital_status:str=Field(min_length=2,max_length=80)
 customer_occupation:str=Field(min_length=2,max_length=120)
 guarantor_postal_code:str=Field(min_length=8,max_length=20)
 activation_fee_cents:int=Field(ge=0)
 contract_end_date:date
 inspection_date:date
 contract_date:date

# Digital inspection of the rented device. A draft can be edited until signed.
class DeviceInspection(Base):
 __tablename__='device_inspections'
 contract_id:Mapped[str]=mapped_column(String(36),primary_key=True)
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 checks_json:Mapped[str]=mapped_column(Text)
 observations:Mapped[str]=mapped_column(Text,default='')
 accessories:Mapped[str]=mapped_column(String(500),default='')
 inspected_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
 inspector_id:Mapped[str]=mapped_column(String(36))

INSPECTION_FIELDS=('screen','touch','cameras','speakers','microphone','buttons','charging','wifi','bluetooth','face_id','battery','body','imei_verified')
class InspectionIn(BaseModel):
 checks:dict[str,str]
 observations:str=Field(default='',max_length=4000)
 accessories:str=Field(default='',max_length=500)

class StoreSettings(Base):
 __tablename__='store_settings'
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),primary_key=True)
 pix_key:Mapped[str]=mapped_column(String(200),default='')
 pix_name:Mapped[str]=mapped_column(String(200),default='')
 pix_qr_path:Mapped[str]=mapped_column(String(500),default='')
 partner_share_pct:Mapped[int]=mapped_column(Integer,default=20)
class PortalCredential(Base):
 __tablename__='portal_credentials'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 customer_id:Mapped[str]=mapped_column(String(36),index=True)
 password_hash:Mapped[str]=mapped_column(String(250))
 __table_args__=(UniqueConstraint('tenant_id','customer_id'),)
class Login(BaseModel): email:str; password:str
class CustomerIn(BaseModel): name:str=Field(min_length=2); cpf:str=Field(pattern=r'^\d{11}$'); phone:str=''; email:str=''; address:str=''
class DeviceIn(BaseModel): model:str=Field(min_length=2); imei:str=Field(pattern=r'^\d{15}$'); cost_cents:int=Field(ge=0); color:str=''; capacity:str=''
class ContractIn(BaseModel): customer_id:str; guarantor_id:Optional[str]=None; device_id:str; installments_count:int=Field(ge=1,le=60); installment_cents:int=Field(ge=1); entry_cents:int=Field(default=0,ge=0); trade_in_cents:int=Field(default=0,ge=0); residual_cents:int=Field(default=0,ge=0); first_due:Optional[datetime]=None
class DocsIn(BaseModel): approved:bool

def db():
 with SessionLocal() as s: yield s

def pw_hash(password):
 salt=secrets.token_hex(16); digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),310000)
 return salt+':'+digest.hex()
def pw_verify(password,stored):
 try:
  salt,digest=stored.split(':'); candidate=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),310000)
  return hmac.compare_digest(candidate.hex(),digest)
 except (ValueError,TypeError): return False

def actor(authorization:Optional[str]=Header(None),s:Session=Depends(db)):
 if not SECRET: raise HTTPException(503,'JWT_SECRET não configurado')
 if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Token ausente')
 try: payload=jwt.decode(authorization[7:],SECRET,algorithms=['HS256'],audience='admin')
 except jwt.PyJWTError: raise HTTPException(401,'Token inválido')
 u=s.get(User,payload.get('sub'))
 if not u or u.tenant_id!=payload.get('tenant'): raise HTTPException(401,'Usuário inválido')
 return u

def scoped(s,cls,identifier,u):
 item=s.scalar(select(cls).where(cls.id==identifier,cls.tenant_id==u.tenant_id))
 if not item: raise HTTPException(404,'Registro não encontrado')
 return item

def audit(s,u,action,target): s.add(Audit(tenant_id=u.tenant_id,actor_id=u.id,action=action,target_id=target))

def production_configuration_errors():
 if os.getenv('APP_ENV','development').lower()!='production': return []
 errors=[]
 if engine.dialect.name!='postgresql': errors.append('PostgreSQL obrigatório em produção')
 if len(SECRET)<32 or SECRET.startswith('COLOQUE_'): errors.append('JWT_SECRET forte obrigatório')
 if not all(os.getenv(k) for k in ('R2_BUCKET','R2_ENDPOINT','R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY')): errors.append('R2 obrigatório')
 origins=[x.strip() for x in os.getenv('CORS_ORIGINS','').split(',') if x.strip()]
 if not origins or '*' in origins or any(not x.startswith('https://') for x in origins): errors.append('CORS deve listar apenas origens HTTPS')
 return errors

@app.on_event('startup')
def validate_production_startup():
 errors=production_configuration_errors()
 if errors: raise RuntimeError('Configuração insegura de produção: '+ '; '.join(errors))

@app.get('/health')
def health(): return {'status':'ok','version':'0.18.0'}
@app.post('/auth/login')
def login(body:Login,s:Session=Depends(db)):
 if not SECRET: raise HTTPException(503,'JWT_SECRET não configurado')
 u=s.scalar(select(User).where(User.email==body.email.lower().strip()))
 if not u or not pw_verify(body.password,u.password_hash): raise HTTPException(401,'Credenciais inválidas')
 token=jwt.encode({'sub':u.id,'tenant':u.tenant_id,'aud':'admin','exp':datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm='HS256')
 return {'access_token':token,'token_type':'bearer','role':u.role}
@app.get('/customers')
def customers(u:User=Depends(actor),s:Session=Depends(db)):
 return [{'id':c.id,'name':c.name,'phone':c.phone,'cpf':c.cpf,'email':c.email,'address':c.address} for c in s.scalars(select(Customer).where(Customer.tenant_id==u.tenant_id)).all()]
@app.post('/customers',status_code=201)
def add_customer(body:CustomerIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 if s.scalar(select(Customer).where(Customer.tenant_id==u.tenant_id,Customer.cpf==body.cpf)): raise HTTPException(409,'CPF já cadastrado')
 c=Customer(tenant_id=u.tenant_id,**body.model_dump());s.add(c);s.flush();audit(s,u,'customer.created',c.id);s.commit();return {'id':c.id}
@app.get('/devices')
def devices(u:User=Depends(actor),s:Session=Depends(db)):
 return [{'id':d.id,'model':d.model,'imei':d.imei,'cost_cents':d.cost_cents,'status':d.status,'capacity':d.capacity,'color':d.color} for d in s.scalars(select(Device).where(Device.tenant_id==u.tenant_id)).all()]
@app.post('/devices',status_code=201)
def add_device(body:DeviceIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 if s.scalar(select(Device).where(Device.tenant_id==u.tenant_id,Device.imei==body.imei)): raise HTTPException(409,'IMEI já cadastrado')
 d=Device(tenant_id=u.tenant_id,**body.model_dump());s.add(d);s.flush();audit(s,u,'device.created',d.id);s.commit();return {'id':d.id}
@app.post('/contracts',status_code=201)
def add_contract(body:ContractIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 scoped(s,Customer,body.customer_id,u)
 if body.guarantor_id: scoped(s,Customer,body.guarantor_id,u)
 d=scoped(s,Device,body.device_id,u)
 if d.status!='available': raise HTTPException(409,'Aparelho indisponível')
 c=Contract(tenant_id=u.tenant_id,**body.model_dump());s.add(c);s.flush();audit(s,u,'contract.draft_created',c.id);s.commit();return {'id':c.id,'status':c.status}
@app.patch('/contracts/{contract_id}/document-review')
def review(contract_id:str,body:DocsIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft': raise HTTPException(409,'Contrato não está em rascunho')
 # Estado informativo; a ativação exige arquivos aprovados individualmente.
 c.documents_approved=body.approved;audit(s,u,'contract.document_review_recorded',c.id);s.commit();return {'documents_approved':c.documents_approved}
@app.post('/contracts/{contract_id}/activate')
def activate(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft': raise HTTPException(409,'Contrato não está em rascunho')
 if os.getenv('APP_ENV','development').lower()=='production':
  template=pathlib.Path(__file__).parent/'contract_template.txt'
  if not template.exists() or not contract_template_issues(template.read_text(encoding='utf-8'))['ready_for_signature']:
   raise HTTPException(409,'Ativação bloqueada: modelo contratual não está finalizado')
 if not c.guarantor_id: raise HTTPException(409,'Fiador obrigatório')
 if not c.signed_at or not c.delivered_at: raise HTTPException(409,'Registrar assinatura e entrega antes de ativar')
 docs=s.scalars(select(Document).where(Document.tenant_id==u.tenant_id,Document.contract_id==c.id)).all()
 latest={}
 for item in sorted(docs,key=lambda d:(d.created_at,d.id)):
  latest[item.kind]=item
 approved={kind for kind,item in latest.items() if item.status=='approved'}
 missing=REQUIRED_DOCUMENTS-approved
 if missing: raise HTTPException(409,{'message':'Documentação obrigatória não aprovada','missing':sorted(missing)})
 d=scoped(s,Device,c.device_id,u)
 if d.status!='available': raise HTTPException(409,'Aparelho indisponível')
 if s.scalar(select(Contract).where(Contract.tenant_id==u.tenant_id,Contract.device_id==d.id,Contract.status=='active')): raise HTTPException(409,'Aparelho já locado')
 if c.trade_in_cents and not s.scalar(select(TradeIn).where(TradeIn.tenant_id==u.tenant_id,TradeIn.contract_id==c.id)): raise HTTPException(409,'Cadastrar aparelho recebido como entrada')
 if not c.first_due: raise HTTPException(409,'Primeiro vencimento obrigatório')
 for i in range(c.installments_count):
  due=month_add(c.first_due,i)
  s.add(Installment(tenant_id=u.tenant_id,contract_id=c.id,number=i+1,amount_cents=c.installment_cents,due_at=due))
 c.status='active'; d.status='rented'; c.documents_approved=True
 audit(s,u,'contract.activated',c.id);s.commit()
 return {'id':c.id,'status':'active','installments_created':c.installments_count}
@app.get('/contracts')
def contracts(u:User=Depends(actor),s:Session=Depends(db)):
 return [{'id':c.id,'status':c.status,'customer_id':c.customer_id,'guarantor_id':c.guarantor_id,'device_id':c.device_id,'documents_approved':c.documents_approved,'installments_count':c.installments_count,'installment_cents':c.installment_cents,'entry_cents':c.entry_cents,'trade_in_cents':c.trade_in_cents,'residual_cents':c.residual_cents,'first_due':c.first_due.isoformat() if c.first_due else None} for c in s.scalars(select(Contract).where(Contract.tenant_id==u.tenant_id)).all()]
@app.post('/installments/{installment_id}/confirm')
def confirm(installment_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Permissão insuficiente')
 p=scoped(s,Installment,installment_id,u)
 if p.status=='paid': raise HTTPException(409,'Parcela já paga')
 contract=scoped(s,Contract,p.contract_id,u)
 if contract.status!='active': raise HTTPException(409,'Pagamento permitido somente para contrato ativo')
 if p.status=='review': raise HTTPException(409,'Comprovante aguardando análise; utilize a aprovação específica')
 p.status='paid';p.paid_at=datetime.now(timezone.utc);p.confirmed_by=u.id;audit(s,u,'installment.manually_confirmed',p.id);s.commit();return {'status':'paid'}

if __name__=='__main__':
 import uvicorn
 uvicorn.run(app,host='127.0.0.1',port=8000)

# ---- CANOG Gestão integrated workflows ----
REQUIRED_DOCUMENTS={'client_video','client_identity','client_residence','client_income','guarantor_video','guarantor_identity','guarantor_residence','guarantor_income'}
STORAGE=pathlib.Path(os.getenv('PRIVATE_STORAGE','./private_uploads')).resolve()
MAX_UPLOAD=30*1024*1024
ALLOWED={'application/pdf','image/jpeg','image/png','image/webp','video/mp4','video/quicktime'}

def file_signature_ok(raw,mime):
 if mime=='application/pdf': return raw.startswith(b'%PDF-')
 if mime=='image/png': return raw.startswith(b'\x89PNG\r\n\x1a\n')
 if mime=='image/jpeg': return raw.startswith(b'\xff\xd8\xff')
 if mime=='image/webp': return raw.startswith(b'RIFF') and raw[8:12]==b'WEBP'
 if mime in ('video/mp4','video/quicktime'): return len(raw)>12 and raw[4:8]==b'ftyp'
 return False

def month_add(dt,n):
 y=dt.year+(dt.month-1+n)//12; m=(dt.month-1+n)%12+1
 return dt.replace(year=y,month=m,day=min(dt.day,calendar.monthrange(y,m)[1]))

def r2_client():
 if not os.getenv('R2_BUCKET'): return None
 import boto3
 required=['R2_ENDPOINT','R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY']
 if any(not os.getenv(k) for k in required): raise RuntimeError('Configuração R2 incompleta')
 return boto3.client('s3',endpoint_url=os.environ['R2_ENDPOINT'],aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto')

def write_private(tenant,raw,suffix):
 if os.getenv('APP_ENV','development').lower()=='production' and not os.getenv('R2_BUCKET'):
  raise HTTPException(503,'Armazenamento privado R2 obrigatório em produção')
 key=f'{tenant}/{uuid.uuid4()}{suffix}'
 client=r2_client()
 if client:
  client.put_object(Bucket=os.environ['R2_BUCKET'],Key=key,Body=raw,ContentType='application/octet-stream',ServerSideEncryption='AES256')
  return 'r2:'+key
 folder=STORAGE/tenant;folder.mkdir(parents=True,exist_ok=True)
 path=folder/(str(uuid.uuid4())+suffix);path.write_bytes(raw)
 return str(path)

def read_private(path):
 if path.startswith('r2:'):
  client=r2_client()
  if not client: raise HTTPException(503,'Armazenamento R2 indisponível')
  try:return client.get_object(Bucket=os.environ['R2_BUCKET'],Key=path[3:])['Body'].read()
  except Exception:raise HTTPException(404,'Arquivo indisponível')
 file=pathlib.Path(path)
 if not file.is_file():raise HTTPException(404,'Arquivo indisponível')
 return file.read_bytes()

class SettingsIn(BaseModel):
 pix_key:str=Field(default='',max_length=200)
 pix_name:str=Field(default='',max_length=200)
 partner_share_pct:int=Field(default=20,ge=0,le=100)
class StatusIn(BaseModel): status:str
class EventIn(BaseModel): signed:bool=False; delivered:bool=False
class SimulateIn(BaseModel):
 price_cents:int=Field(ge=0); cost_cents:int=Field(ge=0)
 entry_cents:int=Field(ge=0); trade_in_cents:int=Field(default=0,ge=0)
 count:int=Field(ge=1,le=60); rate_pct:Decimal=Field(default=Decimal('8'),ge=0,le=100)
 mode:str=Field(default='price',pattern='^(price|negotiated)$')
 negotiated_installment_cents:int|None=Field(default=None,ge=0)
class PortalSetup(BaseModel): customer_id:str; password:str=Field(min_length=10)
class PortalLogin(BaseModel): cpf:str; password:str; tenant_id:str

@app.get('/dashboard')
def dashboard(u:User=Depends(actor),s:Session=Depends(db)):
 contracts=s.scalars(select(Contract).where(Contract.tenant_id==u.tenant_id)).all()
 active={c.id for c in contracts if c.status=='active'}
 installments=s.scalars(select(Installment).where(Installment.tenant_id==u.tenant_id)).all()
 now=datetime.now(timezone.utc)
 open_ps=[p for p in installments if p.contract_id in active and p.status!='paid']
 def aware(dt): return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
 return {'active_contracts':len(active),'draft_contracts':sum(c.status=='draft' for c in contracts),
  'received_cents':sum(p.amount_cents for p in installments if p.status=='paid'),
  'outstanding_cents':sum(p.amount_cents for p in open_ps),
  'overdue_count':sum(aware(p.due_at)<now for p in open_ps),
  'pending_proofs':sum(p.status=='review' for p in open_ps)}

def simulate_financial_schedule(b:SimulateIn):
 """Transparent simulation: Price amortization OR manually negotiated fixed installments.

 Negotiated installments are a commercial price, not an inferred interest rate.
 Neither mode claims to reproduce the unavailable original CANOG formula.
 """
 if b.entry_cents+b.trade_in_cents>b.price_cents:
  raise HTTPException(422,'Entrada total não pode superar o preço')
 principal=b.price_cents-b.entry_cents-b.trade_in_cents
 rows=[]
 if b.mode=='negotiated':
  if b.negotiated_installment_cents is None:
   raise HTTPException(422,'Informe o valor da parcela negociada')
  nominal=b.negotiated_installment_cents
  if nominal*b.count<principal:
   raise HTTPException(422,'Parcelas negociadas não cobrem o saldo financiado; revise os valores')
  # No invented interest/amortization for a negotiated commercial installment.
  rows=[{'number':n,'interest_cents':None,'principal_cents':None,
         'amount_cents':nominal,'remaining_cents':None} for n in range(1,b.count+1)]
  total_installments=nominal*b.count
  total_interest=None
  formula='negotiated_fixed_installment'
  notice='Parcela definida manualmente; o excedente sobre o saldo não é classificado como juros contratuais.'
 else:
  rate=b.rate_pct/Decimal(100)
  if principal==0: nominal=0
  elif rate==0: nominal=int((Decimal(principal)/b.count).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  else:
   amount=Decimal(principal)*rate/(Decimal(1)-(Decimal(1)+rate)**(-b.count))
   nominal=int(amount.quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  balance=principal
  for number in range(1,b.count+1):
   interest=int((Decimal(balance)*rate).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
   due=balance+interest if number==b.count else min(nominal,balance+interest)
   amortization=due-interest
   balance-=amortization
   rows.append({'number':number,'interest_cents':interest,'principal_cents':amortization,
                'amount_cents':due,'remaining_cents':balance})
  total_installments=sum(row['amount_cents'] for row in rows)
  total_interest=total_installments-principal
  formula='price_provisional'
  notice='Tabela Price ilustrativa; taxa por parcela. Não foi validada contra o simulador original.'
 total=b.entry_cents+b.trade_in_cents+total_installments
 gross=total-b.cost_cents
 return {'mode':b.mode,'installment_cents':nominal,'last_installment_cents':rows[-1]['amount_cents'],
  'installments_total_cents':total_installments,'schedule':rows,
  'total_cents':total,'gross_margin_cents':gross,'principal_cents':principal,
  'total_interest_cents':total_interest,
  'commercial_excess_cents':total_installments-principal if b.mode=='negotiated' else None,
  'cash_entry_cents':b.entry_cents,'trade_in_value_cents':b.trade_in_cents,
  'roi_pct':str((Decimal(gross)*100/Decimal(b.cost_cents)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)) if b.cost_cents else None,
  'formula':formula,'validated_against_original':False,
  'rate_basis':'per_installment' if b.mode=='price' else None,
  'notice':notice,
  'margin_notice':'Margem bruta projetada, incluindo valor atribuído ao aparelho de entrada; não é lucro realizado nem fluxo de caixa.'}

@app.post('/simulate')
def simulate(b:SimulateIn,u:User=Depends(actor)):
 return simulate_financial_schedule(b)

@app.get('/installments')
def installments(contract_id:Optional[str]=None,u:User=Depends(actor),s:Session=Depends(db)):
 q=select(Installment).where(Installment.tenant_id==u.tenant_id)
 if contract_id: scoped(s,Contract,contract_id,u);q=q.where(Installment.contract_id==contract_id)
 return [{'id':p.id,'contract_id':p.contract_id,'number':p.number,'amount_cents':p.amount_cents,'due_at':p.due_at.isoformat(),'status':p.status,'proof_id':p.proof_id} for p in s.scalars(q.order_by(Installment.due_at)).all()]

@app.post('/contracts/{contract_id}/events')
def events(contract_id:str,b:EventIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft': raise HTTPException(409,'Contrato não está em rascunho')
 if b.signed: c.signed_at=datetime.now(timezone.utc)
 if b.delivered: c.delivered_at=datetime.now(timezone.utc)
 audit(s,u,'contract.events_recorded',c.id);s.commit()
 return {'signed':bool(c.signed_at),'delivered':bool(c.delivered_at)}

@app.get('/contracts/{contract_id}/documents')
def documents(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Acesso restrito')
 scoped(s,Contract,contract_id,u)
 return [{'id':d.id,'kind':d.kind,'filename':d.filename,'status':d.status,'mime':d.mime} for d in s.scalars(select(Document).where(Document.tenant_id==u.tenant_id,Document.contract_id==contract_id)).all()]

@app.post('/contracts/{contract_id}/documents',status_code=201)
async def upload_document(contract_id:str,kind:str=Form(...),file:UploadFile=File(...),u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft': raise HTTPException(409,'Upload somente em rascunhos')
 if kind not in REQUIRED_DOCUMENTS: raise HTTPException(422,'Categoria inválida')
 if kind.endswith('video') and file.content_type not in ('video/mp4','video/quicktime'): raise HTTPException(415,'Vídeo obrigatório para esta categoria')
 if file.content_type not in ALLOWED: raise HTTPException(415,'Formato não permitido')
 raw=await file.read(MAX_UPLOAD+1)
 if len(raw)>MAX_UPLOAD: raise HTTPException(413,'Arquivo acima do limite de 30 MB')
 if not file_signature_ok(raw,file.content_type): raise HTTPException(415,'Conteúdo do arquivo não corresponde ao formato informado')
 suffix={ 'application/pdf':'.pdf','image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','video/mp4':'.mp4','video/quicktime':'.mov'}[file.content_type]
 path=write_private(u.tenant_id,raw,suffix)
 d=Document(tenant_id=u.tenant_id,contract_id=contract_id,kind=kind,filename=(file.filename or 'arquivo')[:200],path=path,mime=file.content_type,uploaded_by=u.id)
 s.add(d);s.flush();audit(s,u,'document.uploaded',d.id);s.commit();return {'id':d.id,'status':d.status}

@app.patch('/documents/{document_id}/review')
def document_review(document_id:str,b:StatusIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 d=scoped(s,Document,document_id,u)
 if b.status not in ('approved','rejected'): raise HTTPException(422,'Status inválido')
 contract=scoped(s,Contract,d.contract_id,u)
 if contract.status!='draft': raise HTTPException(409,'Revisão somente antes da ativação')
 d.status=b.status;audit(s,u,'document.reviewed',d.id);s.commit();return {'status':d.status}

@app.get('/documents/{document_id}/download')
def document_download(document_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Acesso restrito')
 d=scoped(s,Document,document_id,u)
 return Response(content=read_private(d.path),media_type=d.mime,headers={'Content-Disposition':'attachment; filename="documento"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@app.get('/settings')
def get_settings(u:User=Depends(actor),s:Session=Depends(db)):
 st=s.get(StoreSettings,u.tenant_id)
 return {'pix_key':st.pix_key if st else '', 'pix_name':st.pix_name if st else '', 'partner_share_pct':st.partner_share_pct if st else 20,'has_qr':bool(st and st.pix_qr_path)}
@app.put('/settings')
def put_settings(b:SettingsIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 st=s.get(StoreSettings,u.tenant_id)
 if not st: st=StoreSettings(tenant_id=u.tenant_id);s.add(st)
 st.pix_key=b.pix_key;st.pix_name=b.pix_name;st.partner_share_pct=b.partner_share_pct
 audit(s,u,'settings.updated',u.tenant_id);s.commit();return {'saved':True}
@app.post('/settings/pix-qr')
async def pix_qr(file:UploadFile=File(...),u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 if file.content_type not in ('image/png','image/jpeg','image/webp'): raise HTTPException(415,'Imagem inválida')
 raw=await file.read(2*1024*1024+1)
 if len(raw)>2*1024*1024: raise HTTPException(413,'Imagem grande demais')
 if not file_signature_ok(raw,file.content_type): raise HTTPException(415,'Imagem inválida')
 st=s.get(StoreSettings,u.tenant_id)
 if not st: st=StoreSettings(tenant_id=u.tenant_id);s.add(st)
 st.pix_qr_path=write_private(u.tenant_id,raw,'.png' if file.content_type=='image/png' else '.jpg')
 audit(s,u,'pix.qr_updated',u.tenant_id);s.commit();return {'saved':True}

@app.post('/portal/access')
def portal_access(b:PortalSetup,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 scoped(s,Customer,b.customer_id,u)
 cred=s.scalar(select(PortalCredential).where(PortalCredential.tenant_id==u.tenant_id,PortalCredential.customer_id==b.customer_id))
 if not cred: cred=PortalCredential(tenant_id=u.tenant_id,customer_id=b.customer_id);s.add(cred)
 cred.password_hash=pw_hash(b.password);audit(s,u,'portal.access_set',b.customer_id);s.commit();return {'saved':True}
@app.post('/portal/login')
def portal_login(b:PortalLogin,s:Session=Depends(db)):
 if not SECRET: raise HTTPException(503,'JWT_SECRET não configurado')
 customers=s.scalars(select(Customer).where(Customer.cpf==b.cpf,Customer.tenant_id==b.tenant_id)).all()
 for c in customers:
  cred=s.scalar(select(PortalCredential).where(PortalCredential.customer_id==c.id,PortalCredential.tenant_id==c.tenant_id))
  if cred and pw_verify(b.password,cred.password_hash):
   token=jwt.encode({'sub':c.id,'tenant':c.tenant_id,'aud':'portal','exp':datetime.now(timezone.utc)+timedelta(hours=2)},SECRET,algorithm='HS256')
   return {'access_token':token,'token_type':'bearer'}
 raise HTTPException(401,'Credenciais inválidas')

def portal_actor(authorization:Optional[str]=Header(None),s:Session=Depends(db)):
 if not SECRET or not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Token ausente')
 try: payload=jwt.decode(authorization[7:],SECRET,algorithms=['HS256'],audience='portal')
 except jwt.PyJWTError: raise HTTPException(401,'Token inválido')
 c=s.scalar(select(Customer).where(Customer.id==payload.get('sub'),Customer.tenant_id==payload.get('tenant')))
 if not c: raise HTTPException(401,'Cliente inválido')
 return c
@app.get('/portal/me')
def portal_me(c:Customer=Depends(portal_actor),s:Session=Depends(db)):
 contracts=s.scalars(select(Contract).where(Contract.tenant_id==c.tenant_id,Contract.customer_id==c.id,Contract.status!='draft')).all()
 ids=[x.id for x in contracts]
 installments=s.scalars(select(Installment).where(Installment.tenant_id==c.tenant_id,Installment.contract_id.in_(ids))).all() if ids else []
 st=s.get(StoreSettings,c.tenant_id)
 return {'name':c.name,'contracts':[{'id':x.id,'status':x.status,'installments_count':x.installments_count} for x in contracts],
 'installments':[{'id':p.id,'contract_id':p.contract_id,'number':p.number,'amount_cents':p.amount_cents,'due_at':p.due_at.isoformat(),'status':p.status} for p in installments],
 'pix_key':st.pix_key if st else '','pix_name':st.pix_name if st else '', 'has_qr':bool(st and st.pix_qr_path)}
@app.get('/portal/pix-qr')
def portal_pix_qr(c:Customer=Depends(portal_actor),s:Session=Depends(db)):
 st=s.get(StoreSettings,c.tenant_id)
 if not st or not st.pix_qr_path: raise HTTPException(404,'QR não configurado')
 return Response(content=read_private(st.pix_qr_path),media_type='image/png' if st.pix_qr_path.endswith('.png') else 'image/jpeg',headers={'Cache-Control':'no-store'})
@app.post('/portal/installments/{installment_id}/proof')
async def portal_proof(installment_id:str,file:UploadFile=File(...),c:Customer=Depends(portal_actor),s:Session=Depends(db)):
 p=s.scalar(select(Installment).where(Installment.id==installment_id,Installment.tenant_id==c.tenant_id))
 if not p: raise HTTPException(404,'Parcela não encontrada')
 contract=s.scalar(select(Contract).where(Contract.id==p.contract_id,Contract.tenant_id==c.tenant_id,Contract.customer_id==c.id))
 if not contract or contract.status!='active': raise HTTPException(409,'Comprovante permitido somente para contrato ativo')
 if p.status=='paid': raise HTTPException(409,'Parcela quitada')
 if p.status=='review': raise HTTPException(409,'Comprovante já enviado; aguarde conferência')
 if file.content_type not in ('application/pdf','image/png','image/jpeg'): raise HTTPException(415,'Comprovante inválido')
 raw=await file.read(5*1024*1024+1)
 if len(raw)>5*1024*1024: raise HTTPException(413,'Limite de 5 MB')
 if not file_signature_ok(raw,file.content_type): raise HTTPException(415,'Arquivo inválido')
 d=Document(tenant_id=c.tenant_id,contract_id=contract.id,kind='pix_proof',filename=(file.filename or 'comprovante')[:200],path=write_private(c.tenant_id,raw,'.pdf' if file.content_type=='application/pdf' else '.png' if file.content_type=='image/png' else '.jpg'),mime=file.content_type,uploaded_by=c.id)
 s.add(d);s.flush();p.proof_id=d.id;p.status='review';audit(s,c,'installment.proof_submitted',p.id);s.commit();return {'status':'review'}

@app.get('/contracts/{contract_id}/pdf')
def contract_pdf(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
 from reportlab.lib.styles import getSampleStyleSheet
 from reportlab.lib import colors
 from reportlab.lib.enums import TA_CENTER
 from xml.sax.saxutils import escape
 c=scoped(s,Contract,contract_id,u)
 customer=scoped(s,Customer,c.customer_id,u)
 guarantor=scoped(s,Customer,c.guarantor_id,u) if c.guarantor_id else None
 d=scoped(s,Device,c.device_id,u)
 buffer=io.BytesIO();doc=SimpleDocTemplate(buffer,pagesize=(595,842),topMargin=48,bottomMargin=48)
 styles=getSampleStyleSheet();story=[]
 def para(t):story.append(Paragraph(t,styles['Normal']));story.append(Spacer(1,12))
 story.append(Paragraph('CANOG — FICHA DE DADOS CONTRATUAIS',styles['Title']))
 para('<b>ATENÇÃO: este documento NÃO substitui o contrato jurídico de 16 páginas enviado pela loja. É apenas uma ficha para conferência.</b>')
 for label,val in [('Contrato',c.id),('Situação',c.status),('Locatário',customer.name),('CPF',customer.cpf),('Fiador',guarantor.name if guarantor else 'Não cadastrado'),('Aparelho',d.model+' '+d.capacity+' '+d.color),('IMEI',d.imei),('Entrada (R$)',f'{c.entry_cents/100:.2f}'),('Troca (R$)',f'{c.trade_in_cents/100:.2f}'),('Parcelas',f'{c.installments_count} x R$ {c.installment_cents/100:.2f}'),('Valor residual (R$)',f'{c.residual_cents/100:.2f}'),('Primeiro vencimento',c.first_due.strftime('%d/%m/%Y') if c.first_due else 'Não definido')]: para(f'<b>{escape(label)}:</b> {escape(str(val))}')
 para('A versão final do instrumento contratual deverá incorporar integralmente o modelo fornecido, seus anexos e revisão jurídica.')
 doc.build(story)
 return Response(content=buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="ficha-{contract_id}.pdf"'})


class ReasonIn(BaseModel):
 reason:str=Field(min_length=8,max_length=500)

@app.post('/installments/{installment_id}/reverse')
def reverse_payment(installment_id:str,b:ReasonIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 p=scoped(s,Installment,installment_id,u)
 if p.status!='paid': raise HTTPException(409,'Parcela não está quitada')
 p.status='pending';p.paid_at=None;p.confirmed_by=None
 audit(s,u,'installment.reversed:'+b.reason[:40],p.id);s.commit()
 return {'status':'pending'}

@app.post('/installments/{installment_id}/reject-proof')
def reject_proof(installment_id:str,b:ReasonIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 p=scoped(s,Installment,installment_id,u)
 if p.status!='review': raise HTTPException(409,'Parcela não está aguardando análise')
 proof=scoped(s,Document,p.proof_id,u) if p.proof_id else None
 if proof: proof.status='rejected'
 p.status='pending';p.proof_id=None;audit(s,u,'installment.proof_rejected:'+b.reason[:40],p.id);s.commit()
 return {'status':'pending'}

@app.post('/installments/{installment_id}/approve-proof')
def approve_proof(installment_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 p=scoped(s,Installment,installment_id,u)
 if p.status!='review' or not p.proof_id: raise HTTPException(409,'Parcela não possui comprovante aguardando análise')
 contract=scoped(s,Contract,p.contract_id,u)
 if contract.status!='active': raise HTTPException(409,'Contrato não está ativo')
 proof=scoped(s,Document,p.proof_id,u)
 if proof.contract_id!=contract.id or proof.kind!='pix_proof' or proof.status!='pending':
  raise HTTPException(409,'Comprovante inválido para esta parcela')
 proof.status='approved'
 p.status='paid';p.paid_at=datetime.now(timezone.utc);p.confirmed_by=u.id
 audit(s,u,'installment.proof_approved',p.id);s.commit()
 return {'status':'paid','proof_id':proof.id}

@app.get('/reports/upcoming-due')
def upcoming_due(days:int=7,u:User=Depends(actor),s:Session=Depends(db)):
 # Operational alert: only active contracts, pending/review payments, and tenant-owned data.
 if days<1 or days>31: raise HTTPException(422,'Período deve ser entre 1 e 31 dias')
 today=datetime.now(timezone.utc).date()
 limit=today+timedelta(days=days)
 active_ids=set(s.scalars(select(Contract.id).where(Contract.tenant_id==u.tenant_id,Contract.status=='active')).all())
 pending=s.scalars(select(Installment).where(Installment.tenant_id==u.tenant_id,Installment.status.in_(['pending','review']))).all()
 due=[];overdue=[]
 for item in pending:
  if item.contract_id not in active_ids: continue
  due_date=item.due_at.date()
  record={'installment_id':item.id,'contract_id':item.contract_id,'number':item.number,
          'due_date':due_date.isoformat(),'amount_cents':item.amount_cents,'status':item.status}
  if due_date<today: overdue.append(record)
  elif due_date<=limit: due.append(record)
 return {'days':days,'upcoming':sorted(due,key=lambda x:(x['due_date'],x['contract_id'],x['number'])),
         'overdue':sorted(overdue,key=lambda x:(x['due_date'],x['contract_id'],x['number'])),
         'upcoming_total_cents':sum(x['amount_cents'] for x in due),
         'overdue_total_cents':sum(x['amount_cents'] for x in overdue)}

@app.get('/reports/financial')
def financial_report(u:User=Depends(actor),s:Session=Depends(db)):
 ps=s.scalars(select(Installment).where(Installment.tenant_id==u.tenant_id)).all()
 cs=s.scalars(select(Contract).where(Contract.tenant_id==u.tenant_id)).all()
 ds=s.scalars(select(Device).where(Device.tenant_id==u.tenant_id)).all()
 active_ids={c.id for c in cs if c.status=='active'}
 now=datetime.now(timezone.utc)
 open_ps=[p for p in ps if p.contract_id in active_ids and p.status!='paid']
 return {'received_cents':sum(p.amount_cents for p in ps if p.status=='paid'),
 'receivable_cents':sum(p.amount_cents for p in open_ps),
 'overdue_cents':sum(p.amount_cents for p in open_ps if (p.due_at.replace(tzinfo=timezone.utc) if p.due_at.tzinfo is None else p.due_at)<now),
 'invested_cents':sum(d.cost_cents for d in ds if d.status=='rented'),
 'contracts_by_status':{x:sum(c.status==x for c in cs) for x in ('draft','active','returned','acquired','cancelled')},
 'disclaimer':'Recebimentos incluem apenas parcelas confirmadas. Entradas em dinheiro, trocas e despesas não estão conciliadas. Não interpretar recebimentos como lucro realizado.'}

@app.get('/reports/cost-recovery')
def cost_recovery_report(u:User=Depends(actor),s:Session=Depends(db)):
 """Conservative realized-profit calculation from confirmed installment receipts only.

 Cash down payments are not recognized without an explicit receipt event; trade-ins
 are assets, not cash. Cost recovery precedes realized profit and partner share.
 """
 cs=s.scalars(select(Contract).where(Contract.tenant_id==u.tenant_id,Contract.status!='draft')).all()
 ps=s.scalars(select(Installment).where(Installment.tenant_id==u.tenant_id,Installment.status=='paid')).all()
 ds={d.id:d for d in s.scalars(select(Device).where(Device.tenant_id==u.tenant_id)).all()}
 st=s.get(StoreSettings,u.tenant_id)
 pct=st.partner_share_pct if st else 20
 paid_by_contract={}
 for p in ps: paid_by_contract[p.contract_id]=paid_by_contract.get(p.contract_id,0)+p.amount_cents
 rows=[]
 for c in cs:
  d=ds.get(c.device_id)
  if not d: continue
  received=paid_by_contract.get(c.id,0)
  recovered=min(received,d.cost_cents)
  realized=max(0,received-d.cost_cents)
  partner=realized*pct//100
  rows.append({'contract_id':c.id,'status':c.status,'device_id':d.id,
   'device_cost_cents':d.cost_cents,'confirmed_installments_cents':received,
   'cost_recovered_cents':recovered,'cost_to_recover_cents':max(0,d.cost_cents-received),
   'realized_profit_cents':realized,'partner_share_cents':partner,
   'company_profit_cents':realized-partner})
 return {'partner_share_pct':pct,'contracts':rows,
  'totals':{k:sum(r[k] for r in rows) for k in ('confirmed_installments_cents','cost_recovered_cents','cost_to_recover_cents','realized_profit_cents','partner_share_cents','company_profit_cents')},
  'accounting_scope':'Somente parcelas confirmadas. Entradas em dinheiro, trocas, custos extras, estornos e valor residual exigem conciliação específica antes do lucro definitivo.',
  'is_final_profit':False}

@app.get('/portal/contracts/{contract_id}/summary')
def portal_contract_summary(contract_id:str,c:Customer=Depends(portal_actor),s:Session=Depends(db)):
 contract=s.scalar(select(Contract).where(Contract.id==contract_id,Contract.tenant_id==c.tenant_id,Contract.customer_id==c.id,Contract.status!='draft'))
 if not contract: raise HTTPException(404,'Contrato não encontrado')
 d=s.scalar(select(Device).where(Device.id==contract.device_id,Device.tenant_id==c.tenant_id))
 return {'id':contract.id,'status':contract.status,'device':d.model if d else '',
 'installments_count':contract.installments_count,'installment_cents':contract.installment_cents,
 'entry_cents':contract.entry_cents,'residual_cents':contract.residual_cents}

def contract_template_issues(raw:str):
 """Report template placeholders; do not silently change legally relevant wording."""
 tokens=sorted(set(re.findall(r'\{\{[A-Z_]+\}\}',raw)))
 legacy=[]
 for line_number,line in enumerate(raw.splitlines(),1):
  if re.search(r'X{4,}',line):
   legacy.append({'line':line_number,'excerpt':line.strip()[:140]})
 return {'unresolved_tokens':tokens,'legacy_placeholders':legacy,
         'ready_for_signature':not tokens and not legacy}

def missing_legal_data(contract,customer,guarantor,device,details=None):
 """Shared readiness validation for preview and draft issuance."""
 required=[('customer.name',customer.name),('customer.cpf',customer.cpf),
  ('customer.address',customer.address),('customer.phone',customer.phone),
  ('guarantor',guarantor),('guarantor.address',guarantor.address if guarantor else None),
  ('guarantor.phone',guarantor.phone if guarantor else None),
  ('device.model',device.model),('device.imei',device.imei),
  ('device.color',device.color),('device.capacity',device.capacity),
  ('contract.first_due',contract.first_due)]
 required += [('legal_details',details),('customer.postal_code',details.customer_postal_code if details else None),
  ('customer.marital_status',details.customer_marital_status if details else None),
  ('customer.occupation',details.customer_occupation if details else None),
  ('guarantor.postal_code',details.guarantor_postal_code if details else None),
  ('activation_fee',details.activation_fee_cents if details and details.activation_fee_cents is not None else None),
  ('contract_end_date',details.contract_end_date if details else None),
  ('inspection_date',details.inspection_date if details else None),
  ('contract_date',details.contract_date if details else None)]
 return [name for name,value in required if value is None or value=='' or (isinstance(value,str) and not value.strip())]

@app.get('/admin/deployment-readiness')
def deployment_readiness(u:User=Depends(actor)):
 """Configuration diagnostics only; never return secrets or customer data."""
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 production=os.getenv('APP_ENV','development').lower()=='production'
 template=pathlib.Path(__file__).parent/'contract_template.txt'
 issues=contract_template_issues(template.read_text(encoding='utf-8')) if template.exists() else None
 checks={
  'jwt_secret_configured':len(SECRET)>=32 and not SECRET.startswith('COLOQUE_'),
  'database_postgresql':engine.dialect.name=='postgresql',
  'private_r2_configured':all(os.getenv(k) for k in ('R2_BUCKET','R2_ENDPOINT','R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY')),
  'cors_origins_explicit':bool(os.getenv('CORS_ORIGINS')) and '*' not in os.getenv('CORS_ORIGINS',''),
  'contract_template_present':template.is_file(),
  'contract_template_placeholders_resolved':bool(issues and issues['ready_for_signature']),
 }
 return {'environment':'production' if production else 'development',
         'checks':checks,'configuration_ready':all(checks.values()),
         'legal_template_ready':checks['contract_template_placeholders_resolved'],
         'legal_review_required':True,
         'note':'Diagnóstico estático: não testa conectividade R2, compilação do frontend nem revisão jurídica.'}

@app.put('/contracts/{contract_id}/legal-details')
def update_legal_details(contract_id:str,b:LegalDetailsIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 contract=scoped(s,Contract,contract_id,u)
 if contract.status!='draft': raise HTTPException(409,'Dados jurídicos só podem ser alterados em rascunhos')
 details=s.scalar(select(ContractLegalDetails).where(ContractLegalDetails.contract_id==contract_id,ContractLegalDetails.tenant_id==u.tenant_id))
 if not details:
  details=ContractLegalDetails(contract_id=contract_id,tenant_id=u.tenant_id)
  s.add(details)
 for key,value in b.model_dump().items(): setattr(details,key,value)
 audit(s,u,'contract.legal_details_updated',contract_id)
 s.commit()
 return {'saved':True,'contract_id':contract_id}

@app.get('/contracts/{contract_id}/legal-readiness')
def legal_readiness(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Acesso restrito')
 scoped(s,Contract,contract_id,u)
 template=pathlib.Path(__file__).parent/'contract_template.txt'
 if not template.exists(): raise HTTPException(503,'Modelo contratual não instalado')
 # This endpoint reports source-template defects; it does not certify legal adequacy.
 issues=contract_template_issues(template.read_text(encoding='utf-8'))
 contract=scoped(s,Contract,contract_id,u)
 customer=scoped(s,Customer,contract.customer_id,u)
 guarantor=scoped(s,Customer,contract.guarantor_id,u) if contract.guarantor_id else None
 device=scoped(s,Device,contract.device_id,u)
 details=s.scalar(select(ContractLegalDetails).where(ContractLegalDetails.contract_id==contract_id,ContractLegalDetails.tenant_id==u.tenant_id))
 missing=missing_legal_data(contract,customer,guarantor,device,details)
 return {**issues,'missing_contract_data':missing,
         'ready_for_signature':False, # A software check never replaces legal review.
         'legal_review_required':True,'template_validation_only':True}


def render_legal_preview(raw, contract, customer, guarantor, device, details=None):
 """Render the ORIGINAL legal text as a review copy, exposing all missing fields.
 Never infer absent personal/legal facts or silently alter clauses.
 """
 values={
  'CLIENTE_NOME':customer.name,'CLIENTE_CPF':customer.cpf,
  'CLIENTE_ENDERECO':customer.address,'CLIENTE_TELEFONE':customer.phone,
  'CLIENTE_EMAIL':customer.email,
  'FIADOR_NOME':guarantor.name if guarantor else '',
  'FIADOR_CPF':guarantor.cpf if guarantor else '',
  'FIADOR_ENDERECO':guarantor.address if guarantor else '',
  'APARELHO_MODELO':device.model,'APARELHO_CAPACIDADE':device.capacity,
  'APARELHO_COR':device.color,'APARELHO_IMEI':device.imei,
  'PRAZO_MESES':str(contract.installments_count),
  'ENTRADA':f'{contract.entry_cents/100:.2f}',
  'PARCELAS':str(contract.installments_count),
  'PARCELA_VALOR':f'{contract.installment_cents/100:.2f}',
  'VALOR_RESIDUAL':f'{contract.residual_cents/100:.2f}',
  'PRIMEIRO_VENCIMENTO':contract.first_due.strftime('%d/%m/%Y') if contract.first_due else '',
  'DATA_CONTRATO':details.contract_date.strftime('%d/%m/%Y') if details and details.contract_date else '',
  'CLIENTE_CEP':details.customer_postal_code if details else '',
  'CLIENTE_ESTADO_CIVIL':details.customer_marital_status if details else '',
  'CLIENTE_PROFISSAO':details.customer_occupation if details else '',
  'FIADOR_CEP':details.guarantor_postal_code if details else '',
  'TAXA_ATIVACAO':f'{details.activation_fee_cents/100:.2f}' if details and details.activation_fee_cents is not None else '',
  'DATA_TERMINO':details.contract_end_date.strftime('%d/%m/%Y') if details and details.contract_end_date else '',
  'DATA_VISTORIA':details.inspection_date.strftime('%d/%m/%Y') if details and details.inspection_date else '',
 }
 missing=[]
 def replace_token(match):
  key=match.group(1)
  value=values.get(key,'')
  if not str(value).strip():
   missing.append(key)
   return '[PENDENTE: '+key+']'
  return str(value)
 raw=re.sub(r'\{\{([A-Z_]+)\}\}',replace_token,raw)
 # Existing legacy placeholders are NOT assigned to a guessed field.
 # They remain explicitly flagged for manual review.
 def replace_legacy(match):
  missing.append('CAMPO_GENERICO_ORIGINAL')
  return '[PENDENTE: CAMPO ORIGINAL]'
 raw=re.sub(r'X{4,}',replace_legacy,raw)
 if 'XX-DATA-VISTORIA' in raw:
  missing.append('DATA_VISTORIA')
  raw=raw.replace('XX-DATA-VISTORIA','[PENDENTE: DATA_VISTORIA]')
 return raw,sorted(set(missing))

INSPECTION_LABELS = {
 'screen':'Tela', 'touch':'Toque', 'cameras':'Câmeras',
 'speakers':'Alto-falantes', 'microphone':'Microfone', 'buttons':'Botões',
 'charging':'Carregamento', 'wifi':'Wi-Fi', 'bluetooth':'Bluetooth',
 'face_id':'Face ID', 'battery':'Bateria', 'body':'Conservação externa',
 'imei_verified':'IMEI conferido',
}
INSPECTION_STATUSES = {'ok':'Conforme', 'issue':'Com ressalva', 'not_tested':'Não testado'}

def inspection_pdf_appendix(inspection):
 """A supplementary report, not a replacement for the original Annex I."""
 if inspection is None:
  return ['VISTORIA DIGITAL NÃO REGISTRADA — conferir Anexo I manualmente.']
 checks=json.loads(inspection.checks_json)
 rows=['RELATÓRIO COMPLEMENTAR DA VISTORIA DIGITAL',
       'Este relatório complementa o Anexo I original e não substitui assinaturas ou campos de vistoria não registrados.']
 for key in INSPECTION_FIELDS:
  rows.append(f'{INSPECTION_LABELS[key]}: {INSPECTION_STATUSES.get(checks.get(key), "Sem registro")}')
 rows.extend(['Acessórios: '+(inspection.accessories or 'Não informados'),
              'Observações: '+(inspection.observations or 'Nenhuma registrada'),
              'Registrado em: '+inspection.inspected_at.strftime('%d/%m/%Y %H:%M UTC')])
 return rows

def add_inspection_to_review_text(raw,inspection):
 """Preserve every original contract clause and append a clearly identified report."""
 return raw + '\n[[PAGE_BREAK]]\n' + '\n'.join(inspection_pdf_appendix(inspection))

@app.get('/contracts/{contract_id}/review-copy.pdf')
def contract_review_copy(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 """Watermarked complete-text review PDF; NEVER a signed or final contract."""
 if u.role!='admin': raise HTTPException(403,'Acesso restrito')
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.lib.pagesizes import A4
 from reportlab.lib import colors
 from xml.sax.saxutils import escape
 c=scoped(s,Contract,contract_id,u)
 customer=scoped(s,Customer,c.customer_id,u)
 guarantor=scoped(s,Customer,c.guarantor_id,u) if c.guarantor_id else None
 device=scoped(s,Device,c.device_id,u)
 template=pathlib.Path(__file__).parent/'contract_template.txt'
 if not template.is_file(): raise HTTPException(503,'Modelo contratual não instalado')
 details=s.scalar(select(ContractLegalDetails).where(ContractLegalDetails.contract_id==c.id,ContractLegalDetails.tenant_id==u.tenant_id))
 raw,missing=render_legal_preview(template.read_text(encoding='utf-8'),c,customer,guarantor,device,details)
 inspection=s.scalar(select(DeviceInspection).where(DeviceInspection.contract_id==c.id,DeviceInspection.tenant_id==u.tenant_id))
 raw=add_inspection_to_review_text(raw,inspection)
 out=io.BytesIO()
 doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=45,rightMargin=45,topMargin=60,bottomMargin=55)
 title=ParagraphStyle('review-title',fontName='Helvetica-Bold',fontSize=10,leading=14,spaceAfter=10)
 body=ParagraphStyle('review-body',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=5)
 warn=ParagraphStyle('review-warn',parent=body,textColor=colors.HexColor('#991b1b'))
 story=[Paragraph('CÓPIA PARA CONFERÊNCIA — NÃO ASSINAR',title),
        Paragraph('Texto integral do modelo original, sem aprovação jurídica. Campos pendentes: '+escape(', '.join(missing) or 'nenhum marcador detectado')+'.',warn),Spacer(1,12)]
 for line in raw.splitlines():
  line=line.strip()
  if line=='[[PAGE_BREAK]]': story.append(PageBreak());continue
  if not line: story.append(Spacer(1,5));continue
  story.append(Paragraph(escape(line),title if line.startswith(('CLÁUSULA','ANEXO I','CONTRATO DE LOCAÇÃO')) else body))
 def stamp(canvas,doc):
  canvas.saveState()
  canvas.setFont('Helvetica-Bold',9);canvas.setFillColor(colors.HexColor('#991b1b'))
  canvas.drawString(45,35,'NÃO ASSINAR — CÓPIA PARA CONFERÊNCIA')
  canvas.setFont('Helvetica',8);canvas.drawRightString(550,35,f'Página {doc.page}')
  canvas.restoreState()
 doc.build(story,onFirstPage=stamp,onLaterPages=stamp)
 audit(s,u,'contract.review_copy_generated',c.id);s.commit()
 return Response(content=out.getvalue(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="conferencia-{c.id}.pdf"','Cache-Control':'no-store'})

@app.get('/contracts/{contract_id}/legal-draft.pdf')
def legal_draft(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Acesso restrito')
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.lib.enums import TA_CENTER
 from reportlab.lib import colors
 from reportlab.lib.pagesizes import A4
 from xml.sax.saxutils import escape
 c=scoped(s,Contract,contract_id,u)
 customer=scoped(s,Customer,c.customer_id,u)
 guarantor=scoped(s,Customer,c.guarantor_id,u) if c.guarantor_id else None
 device=scoped(s,Device,c.device_id,u)
 details=s.scalar(select(ContractLegalDetails).where(ContractLegalDetails.contract_id==c.id,ContractLegalDetails.tenant_id==u.tenant_id))
 missing=missing_legal_data(c,customer,guarantor,device,details)
 if missing: raise HTTPException(422,{'message':'Dados contratuais obrigatórios ausentes','missing_contract_data':missing})
 template=pathlib.Path(__file__).parent/'contract_template.txt'
 if not template.exists(): raise HTTPException(503,'Modelo contratual não instalado')
 raw,unresolved=render_legal_preview(template.read_text(encoding='utf-8'),c,customer,guarantor,device,details)
 if unresolved: raise HTTPException(422,{'message':'Campos contratuais não preenchidos','fields':unresolved})
 issues=contract_template_issues(raw)
 if not issues['ready_for_signature']: raise HTTPException(422,{'message':'Marcadores não resolvidos no contrato','issues':issues})
 out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=46,rightMargin=46,topMargin=52,bottomMargin=46)
 title=ParagraphStyle('heading',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceAfter=12)
 body=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=6)
 warning=ParagraphStyle('warn',parent=body,textColor=colors.HexColor('#b91c1c'))
 story=[Paragraph('MINUTA AUTOMÁTICA — REVISÃO JURÍDICA OBRIGATÓRIA',warning),Spacer(1,12)]
 for line in raw.splitlines():
  line=line.strip()
  if not line:story.append(Spacer(1,7));continue
  if line=='[[PAGE_BREAK]]':story.append(PageBreak());continue
  style=title if line.startswith(('CLÁUSULA','ANEXO I','CONTRATO DE LOCAÇÃO')) else body
  story.append(Paragraph(escape(line),style))
 def footer(canvas,doc):
  canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.grey)
  canvas.drawString(46,24,'CANOG — minuta não assinada; conferir campos e cláusulas antes de uso')
  canvas.drawRightString(550,24,str(doc.page));canvas.restoreState()
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 return Response(content=out.getvalue(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="minuta-{c.id}.pdf"'})


# Trade-in is inventory acquisition; the negotiated allowance is NOT cash received.
class TradeIn(Base):
 __tablename__='trade_ins'
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 tenant_id:Mapped[str]=mapped_column(ForeignKey('tenants.id'),index=True)
 contract_id:Mapped[str]=mapped_column(String(36),unique=True)
 device_id:Mapped[str]=mapped_column(String(36),unique=True)
 allowance_cents:Mapped[int]=mapped_column(Integer)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class TradeInIn(BaseModel):
 model:str=Field(min_length=2,max_length=120)
 imei:str=Field(pattern=r'^\d{15}$')
 cost_cents:int=Field(ge=0)
 color:str=''
 capacity:str=''

@app.post('/contracts/{contract_id}/trade-in',status_code=201)
def trade_in(contract_id:str,b:TradeInIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin':raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft':raise HTTPException(409,'Troca somente em rascunho')
 if c.trade_in_cents<=0:raise HTTPException(409,'Contrato sem entrada em aparelho')
 if b.cost_cents!=c.trade_in_cents:raise HTTPException(422,'Avaliação do aparelho diferente da entrada negociada')
 if s.scalar(select(TradeIn).where(TradeIn.tenant_id==u.tenant_id,TradeIn.contract_id==c.id)):raise HTTPException(409,'Troca já cadastrada')
 if s.scalar(select(Device).where(Device.tenant_id==u.tenant_id,Device.imei==b.imei)):raise HTTPException(409,'IMEI já cadastrado')
 d=Device(tenant_id=u.tenant_id,model=b.model,imei=b.imei,cost_cents=b.cost_cents,color=b.color,capacity=b.capacity,status='available')
 s.add(d);s.flush()
 t=TradeIn(tenant_id=u.tenant_id,contract_id=c.id,device_id=d.id,allowance_cents=c.trade_in_cents)
 s.add(t);audit(s,u,'trade_in.received',c.id);s.commit()
 return {'device_id':d.id,'allowance_cents':t.allowance_cents}

class CloseIn(BaseModel):
 action:str=Field(pattern=r'^(return|acquire)$')
 residual_paid:bool=False
 transfer_signed:bool=False

@app.post('/contracts/{contract_id}/close')
def close_contract(contract_id:str,b:CloseIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin':raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='active':raise HTTPException(409,'Contrato não está ativo')
 device=scoped(s,Device,c.device_id,u)
 if b.action=='acquire':
  pending=s.scalar(select(Installment).where(Installment.tenant_id==u.tenant_id,Installment.contract_id==c.id,Installment.status!='paid'))
  if pending:raise HTTPException(409,'Existem parcelas não quitadas')
  if not b.residual_paid or not b.transfer_signed:raise HTTPException(409,'Confirmar valor residual e termo de transferência assinado')
  c.status='acquired';device.status='sold'
 else:
  c.status='returned';device.status='available'
 audit(s,u,'contract.'+c.status,c.id);s.commit()
 return {'status':c.status,'device_status':device.status}

@app.get('/audit')
def audit_log(u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin':raise HTTPException(403,'Apenas administrador')
 logs=s.scalars(select(Audit).where(Audit.tenant_id==u.tenant_id).order_by(Audit.at.desc()).limit(250)).all()
 return [{'action':a.action,'target_id':a.target_id,'at':a.at.isoformat(),'actor_id':a.actor_id} for a in logs]

@app.put('/contracts/{contract_id}/inspection')
def save_inspection(contract_id:str,b:InspectionIn,u:User=Depends(actor),s:Session=Depends(db)):
 if u.role!='admin': raise HTTPException(403,'Apenas administrador')
 c=scoped(s,Contract,contract_id,u)
 if c.status!='draft': raise HTTPException(409,'Vistoria só pode ser alterada em rascunhos')
 if set(b.checks)!=set(INSPECTION_FIELDS):
  raise HTTPException(422,{'message':'Preencher todos os itens da vistoria','required':INSPECTION_FIELDS})
 if any(v not in ('ok','issue','not_tested') for v in b.checks.values()):
  raise HTTPException(422,'Situação de vistoria inválida')
 if any(v=='issue' for v in b.checks.values()) and not b.observations.strip():
  raise HTTPException(422,'Descreva os problemas encontrados na vistoria')
 inspection=s.get(DeviceInspection,c.id)
 if not inspection:
  inspection=DeviceInspection(contract_id=c.id,tenant_id=u.tenant_id,inspector_id=u.id,checks_json='{}')
  s.add(inspection)
 inspection.checks_json=json.dumps(b.checks,sort_keys=True)
 inspection.observations=b.observations.strip()
 inspection.accessories=b.accessories.strip()
 inspection.inspected_at=datetime.now(timezone.utc)
 inspection.inspector_id=u.id
 audit(s,u,'contract.inspection_saved',c.id);s.commit()
 return {'saved':True,'contract_id':c.id}

@app.get('/contracts/{contract_id}/inspection')
def get_inspection(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 scoped(s,Contract,contract_id,u)
 i=s.scalar(select(DeviceInspection).where(DeviceInspection.contract_id==contract_id,DeviceInspection.tenant_id==u.tenant_id))
 if not i: return {'completed':False,'checks':{},'observations':'','accessories':''}
 checks=json.loads(i.checks_json)
 return {'completed':set(checks)==set(INSPECTION_FIELDS) and all(v in ('ok','issue','not_tested') for v in checks.values()),
         'checks':checks,'observations':i.observations,'accessories':i.accessories,
         'inspected_at':i.inspected_at.isoformat(),'inspector_id':i.inspector_id}

@app.get('/contracts/{contract_id}/checklist')
def checklist(contract_id:str,u:User=Depends(actor),s:Session=Depends(db)):
 c=scoped(s,Contract,contract_id,u)
 docs=s.scalars(select(Document).where(Document.tenant_id==u.tenant_id,Document.contract_id==c.id)).all()
 # The most recent upload for each category determines whether the requirement is satisfied.
 # An approved older document must not override a newer pending/rejected replacement.
 latest={}
 for d in sorted(docs,key=lambda x:(x.created_at,x.id)):
  latest[d.kind]=d
 approved={kind for kind,d in latest.items() if d.status=='approved'}
 inspection=s.scalar(select(DeviceInspection).where(DeviceInspection.contract_id==c.id,DeviceInspection.tenant_id==u.tenant_id))
 return {'inspection_completed':bool(inspection and set(json.loads(inspection.checks_json))==set(INSPECTION_FIELDS) and all(v in ('ok','issue','not_tested') for v in json.loads(inspection.checks_json).values())),'missing_documents':sorted(REQUIRED_DOCUMENTS-approved),'signed':bool(c.signed_at),'delivered':bool(c.delivered_at),'has_guarantor':bool(c.guarantor_id),'first_due_set':bool(c.first_due),'status':c.status}
