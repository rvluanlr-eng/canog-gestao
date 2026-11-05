from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'frontend' / 'src' / 'main.jsx'

def test_portal_proof_isolated_from_admin_refresh():
    code = SOURCE.read_text(encoding='utf-8')
    start = code.index('async function sendPortalProof(')
    end = code.index('\nconst field=', start)
    section = code[start:end]
    assert "await req('/portal/installments/'" in section
    assert "await req('/portal/me',{auth:portalToken})" in section
    assert 'setMe(updated)' in section
    assert 'await refresh()' not in section
    assert 'act(()=>req(\'/portal/installments/\'' not in code
    assert 'sendPortalProof(p.id,e.target.files?.[0])' in code
