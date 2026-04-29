class AuditLogger:
    def __init__(self):
        self.events = []
    def log(self, event_type: str, **payload):
        self.events.append({"event": event_type, **payload})
