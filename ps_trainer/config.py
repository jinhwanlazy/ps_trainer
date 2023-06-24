from .db import DBTable

class Config(DBTable):
    def __init__(self):
        super().__init__('configs')

    def __getitem__(self, key):
        item = self.db.execute('SELECT value FROM config WHERE key = ?', (key,))
        if item is None or len(item) == 0:
            return None
        return item[0][0]

    def __setitem__(self, key, value):
        self.db.execute('REPLACE INTO config (key, value) VALUES (?,?)', (key, value))
        self.db.commit()

    def __contains__(self, key):
        return self[key] is not None

    def keys(self):
        for row in self.db.execute('SELECT key FROM config'):
            yield row[0]

    @property
    def current_user(self):
        return self['current_user']

    @current_user.setter
    def current_user(self, name):
        self['current_user'] = name

    @property
    def time_limit(self):
        if 'time_limit' not in self:
            self['time_limit'] = 3600  # default to 1 hour
        return int(self['time_limit'])

    @time_limit.setter
    def time_limit(self, tl):
        self['time_limit'] = tl

    def initialize(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS config (key TEXT UNIQUE, value TEXT)")
        self.db.commit()

