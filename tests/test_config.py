from hibachi_mm.config import load_env_credentials

def test_env_loading(monkeypatch):
    monkeypatch.setenv('HIBACHI_API_KEY_PRODUCTION','k')
    monkeypatch.setenv('HIBACHI_PRIVATE_KEY_PRODUCTION','p')
    monkeypatch.setenv('HIBACHI_ACCOUNT_ID_PRODUCTION','a')
    creds = load_env_credentials('production')
    assert creds['api_key']=='k' and creds['private_key']=='p' and creds['account_id']=='a'
