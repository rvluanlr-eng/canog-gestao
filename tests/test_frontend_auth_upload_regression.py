from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1] / 'frontend' / 'src' / 'main.jsx'


def test_upload_resets_form_after_success_without_relying_on_api_body():
    code = FRONTEND.read_text()
    upload = code.split('async function upload(e){', 1)[1].split('\n', 1)[0]
    assert "await req('/contracts/'+id+'/documents'" in upload
    assert 'formElement.reset()' in upload
    assert 'if(r)' not in upload
    assert upload.index('await req(') < upload.index('formElement.reset()')


def test_login_does_not_refresh_with_stale_access_token():
    code = FRONTEND.read_text()
    for name in ('signIn', 'signPortal'):
        fn = code.split(f'async function {name}(e){{', 1)[1].split('\n', 1)[0]
        assert 'await act(' not in fn
        assert 'setError(e.message)' in fn
