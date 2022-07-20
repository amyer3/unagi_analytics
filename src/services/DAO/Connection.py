

class Connection:
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.database = kwargs['database']
        self.status = ''
        self.connectionObject = {}

    def connect(self):
        pass

    def check_status(self):
        pass



