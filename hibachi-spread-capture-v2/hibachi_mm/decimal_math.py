from decimal import Decimal, ROUND_DOWN
BPS=Decimal('10000'); HUNDRED=Decimal('100'); ZERO=Decimal('0'); ONE=Decimal('1')
def D(v): return v if isinstance(v,Decimal) else Decimal(str(v))
def clamp(v,a,b): return min(max(v,a),b)
def floor_to_step(v,s): return (v/s).to_integral_value(rounding=ROUND_DOWN)*s
def bps(x,mid): return ZERO if mid==ZERO else x/mid*BPS
