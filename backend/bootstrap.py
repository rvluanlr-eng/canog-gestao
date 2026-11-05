"""Run once on an empty database, with environment variables set."""
import os
from sqlalchemy import select
from main import Base,engine,SessionLocal,Tenant,User,pw_hash
email=os.environ['ADMIN_EMAIL'].strip().lower()
password=os.environ['ADMIN_PASSWORD']
if len(password)<12: raise ValueError('ADMIN_PASSWORD deve ter ao menos 12 caracteres')
Base.metadata.create_all(engine)
with SessionLocal() as s:
 if s.scalar(select(User).where(User.email==email)): raise SystemExit('Administrador já existe')
 t=Tenant(name=os.getenv('TENANT_NAME','CANOG iPhones BM'));s.add(t);s.flush()
 s.add(User(tenant_id=t.id,email=email,password_hash=pw_hash(password),role='admin'));s.commit()
 print('Empresa e administrador criados. Não compartilhe a senha.')
