import pytest
pytest.importorskip('fastapi')
from fastapi.testclient import TestClient
from hibachi_mm.dashboard import create_app
from hibachi_mm.dashboard_store import DashboardStore

def test_dashboard_api_works():
    s=DashboardStore(); s.update(x=1)
    c=TestClient(create_app(s))
    assert c.get('/api/dashboard').json()['x']==1

def test_dashboard_websocket_works():
    s=DashboardStore(); s.update(y=2)
    c=TestClient(create_app(s))
    with c.websocket_connect('/ws/dashboard') as ws:
        msg=ws.receive_json()
        assert msg['y']==2
