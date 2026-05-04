class DashboardStore:
    def __init__(self):
        self.snapshot={"ok":True,"mode":"dry-run"}; self.events=[]
    def push(self,e):
        self.events.append(e)
        self.events=self.events[-500:]
