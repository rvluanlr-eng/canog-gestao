"""Pure calculation tests: cent reconciliation and strict provisional designation."""
from pathlib import Path
import subprocess,sys
BACKEND=Path(__file__).resolve().parents[1]/'backend'
SCRIPT=r'''
import os,sys,tempfile
from decimal import Decimal
with tempfile.TemporaryDirectory() as d:
 os.environ.update(DATABASE_URL='sqlite:///'+d+'/db.sqlite',JWT_SECRET='D'*48,PRIVATE_STORAGE=d+'/uploads')
 sys.path.insert(0,sys.argv[1])
 from main import SimulateIn,simulate_financial_schedule
 for principal,count,rate in [(10000,3,'0'),(99999,12,'8'),(100,60,'100'),(0,10,'8'),(1,60,'0'),(123456,24,'1.5')]:
  data=SimulateIn(price_cents=principal,cost_cents=50000,entry_cents=0,trade_in_cents=0,count=count,rate_pct=Decimal(rate))
  result=simulate_financial_schedule(data)
  assert len(result['schedule'])==count
  assert result['schedule'][-1]['remaining_cents']==0
  assert sum(x['principal_cents'] for x in result['schedule'])==principal
  assert sum(x['amount_cents'] for x in result['schedule'])==result['installments_total_cents']
  assert sum(x['interest_cents'] for x in result['schedule'])==result['total_interest_cents']
  assert all(x['remaining_cents']>=0 for x in result['schedule'])
  assert result['validated_against_original'] is False
 print('PASS: six amortization scenarios, reconciliation, provisional flag')
'''
def test_financial_schedule():
 r=subprocess.run([sys.executable,'-c',SCRIPT,str(BACKEND)],capture_output=True,text=True,timeout=45)
 assert r.returncode==0,r.stdout+'\n'+r.stderr
