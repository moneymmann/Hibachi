class DashboardStore:
    def __init__(self):
        self.latest = {}
    def update(self, **kwargs):
        self.latest.update(kwargs)
