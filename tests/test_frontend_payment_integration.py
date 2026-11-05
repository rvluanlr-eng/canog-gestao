"""Verify that the React financial actions match the tested API workflow."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def test_payment_actions_match_backend():
    ui=(ROOT/'frontend/src/main.jsx').read_text()
    api=(ROOT/'backend/main.py').read_text()
    for action in ('approve-proof','reject-proof','confirm','reverse'):
        assert f"'/installments/'+p.id+'/{action}'" in ui
        assert f"@app.post('/installments/{{installment_id}}/{action}')" in api
    assert "p.status==='pending'&&<button" in ui
    assert "p.status==='review'&&<>" in ui
    assert 'Aprovar comprovante e quitar' in ui
    assert 'Confirmar recebimento manual' in ui
