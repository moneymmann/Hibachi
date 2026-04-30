from hibachi_mm.config import d
from decimal import Decimal

def test_decimal(): assert d('1.2')==Decimal('1.2')
