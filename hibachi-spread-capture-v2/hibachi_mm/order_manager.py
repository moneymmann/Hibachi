def validate_live_gate(mode:str)->None:
    import os
    if mode in {'live','live-ui'} and os.getenv('HIBACHI_ENABLE_LIVE_TRADING')!='I_UNDERSTAND_PERP_RISK':
        raise SystemExit('HIBACHI_ENABLE_LIVE_TRADING gate missing')
