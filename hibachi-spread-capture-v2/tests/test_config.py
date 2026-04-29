from hibachi_mm.config import load_config
def test_config_loads(): c=load_config('config.example.yaml'); assert c.exchange.symbol=='BTC/USDT-P'
