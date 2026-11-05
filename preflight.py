"""Offline, read-only release preflight. Run: python preflight.py"""
from pathlib import Path
import json, os, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent
checks=[]
def check(name, ok, detail):
    checks.append({'check':name,'passed':bool(ok),'detail':detail})
frontend=ROOT/'frontend'
backend=ROOT/'backend'
for f in ['main.py','requirements.txt','contract_template.txt']:
    check('backend/'+f,(backend/f).is_file(),'Arquivo obrigatório')
for f in ['package.json','index.html','src/main.jsx']:
    check('frontend/'+f,(frontend/f).is_file(),'Arquivo obrigatório')
try:
    p=json.loads((frontend/'package.json').read_text())
    check('comando de build',bool(p.get('scripts',{}).get('build')),'package.json scripts.build')
except Exception as e: check('package.json válido',False,str(e))
check('dependências frontend instaladas',(frontend/'node_modules'/'vite').exists(),'vite disponível localmente')
check('node disponível',shutil.which('node') is not None,'Executável node')
check('npm disponível',shutil.which('npm') is not None,'Executável npm')
for k in ['DATABASE_URL','JWT_SECRET','CORS_ORIGINS']:
    check('ambiente '+k,bool(os.getenv(k)), 'Variável presente no ambiente de execução')
check('segredo JWT com 32+ caracteres',len(os.getenv('JWT_SECRET',''))>=32,'Comprimento mínimo; não exibe o segredo')
report={'ready_for_release':all(x['passed'] for x in checks),'checks':checks}
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['ready_for_release'] else 1)
