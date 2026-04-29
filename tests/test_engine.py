from hibachi_mm.engine import Engine

def test_dry_run_never_places_order():
    e=Engine('dry-run')
    assert e.dry_run_place_order()['submitted'] is False
