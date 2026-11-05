from decimal import Decimal
import os,sys,tempfile,subprocess
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
from decimal import Decimal
from fastapi import HTTPException
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='D'*48,PRIVATE_STORAGE=d+'/uploads')
 sys.path.insert(0,sys.argv[1])
 from main import SimulateIn,simulate_financial_schedule
 def run(**kw):
  return simulate_financial_schedule(SimulateIn(price_cents=250000,cost_cents=180000,entry_cents=87500,trade_in_cents=0,count=12,rate_pct=Decimal('8'),**kw))
 result=run(mode='negotiated',negotiated_installment_cents=26500)
 assert result['principal_cents']==162500
 assert result['installments_total_cents']==318000
 assert result['total_cents']==405500
 assert result['gross_margin_cents']==225500
 assert result['total_interest_cents'] is None
 assert result['validated_against_original'] is False
 assert all(x['amount_cents']==26500 for x in result['schedule'])
 price=run(mode='price')
 assert price['installment_cents']!=26500
 assert price['schedule'][-1]['remaining_cents']==0
 for kwargs in [dict(mode='negotiated'),dict(mode='negotiated',negotiated_installment_cents=10000)]:
  try:run(**kwargs)
  except HTTPException as e:assert e.status_code==422
  else:raise AssertionError('Missing validation')
 try:simulate_financial_schedule(SimulateIn(price_cents=100,cost_cents=100,entry_cents=101,trade_in_cents=0,count=2,rate_pct=Decimal('0'),mode='price'))
 except HTTPException as e:assert e.status_code==422
 else:raise AssertionError('Entry greater than price accepted')
 print('PASS: negotiated reference, price mode, safeguards')
'''
def test_simulator_modes():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=45)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
