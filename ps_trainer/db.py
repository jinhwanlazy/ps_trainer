import os
import json
import atexit
from datetime import datetime
from collections import Counter

import logging
logger = logging.getLogger(__name__)

import requests
import pandas as pd
import sqlite3
sqlite3.register_converter('DATETIME', sqlite3.converters['TIMESTAMP'])


from . import __datadir__
from .utils import cf_get_all_problems, cf_get_submissions


def assert_connection(fn):
    def wrapped_fn(self, *args, **kwargs):
        assert self.conn is not None
        return fn(self, *args, **kwargs)
    return wrapped_fn


class DBConnection:
    def connect(self):
        pass
    
    def execute(self, query, parameters=None):
        pass
    
    def commit(self):
        pass
    
    def close(self):
        pass


class SQLiteConnection(DBConnection):
    def __init__(self, database_path):
        self.database_path = database_path
        self.connection = None
        
    def connect(self):
        self.connection = sqlite3.connect(self.database_path, detect_types=sqlite3.PARSE_DECLTYPES)
        
    def execute(self, query, parameters=None):
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    
    def commit(self):
        self.connection.commit()
    
    def close(self):
        logger.debug('sqlite.close() called')
        self.connection.close()


# global variable is effectivly a singleton. just don't reassign on it
__db = SQLiteConnection(os.path.join(__datadir__, 'db.sqlite'))
__db.connect()
atexit.register(__db.close)


def get_db():
    return __db


class DBTable:
    def __init__(self, table_name):
        self.db = get_db()
        self.table_name = table_name
        self.initialize()

    def initialize(self):
        raise NotImplementedError


class ProblemDB(DBTable):
    def __init__(self):
        super().__init__('problems')

    def __len__(self):
        res = self.db.execute('SELECT COUNT(1) FROM problems')[0][0]
        return res

    def get_problem(self, pid):
        return self.get_problems_with_pids([pid]).iloc[0]

    def get_problems_with_pids(self, pids):
        if isinstance(pids, str):
            pids = [pids]
        pids_sql = ', '.join(f'"{pid}"' for pid in pids)
        pid_order = {pid: i for i, pid in enumerate(pids)}
        res = self.db.execute(f'SELECT * FROM problems WHERE pid IN ({pids_sql})')
        df = self.__to_df(res)
        df = df.sort_values(by='pid',
                            key=lambda series: series.apply(pid_order.__getitem__),
                            ignore_index=True)
        return df

    def get_problems_with_rating_range(self, min_rating, max_rating):
        res = self.db.execute(
            f'SELECT * FROM problems WHERE ? <= rating AND rating <= ?',
            (min_rating, max_rating),
        )
        return self.__to_df(res)

    @staticmethod
    def __to_df(res):
        df = pd.DataFrame(res, columns=['pid', 'name', 'rating', 'tags'])
        df['tags'] = df.tags.map(json.loads)
        return df
        
    def initialize(self):
        # create table
        self.db.execute((
            'CREATE TABLE IF NOT EXISTS problems ('
                'pid TEXT PRIMARY KEY, '
                'name TEXT, '
                'rating REAL, '
                'tags TEXT'
            ');'
        ))
        self.db.commit()

        # fill table with data from api
        df = cf_get_all_problems()
        if df is None:
            return
        df = df[(df.type == 'PROGRAMMING') & ~df.rating.isna()]
        df = df.sort_values(by=['contestId', 'index'], ignore_index=True)

        old_pids = self.__all_pids()
        for i, row in df.iterrows():
            pid = str(row.contestId) + '/' + row['index'].upper()
            if pid in old_pids:
                continue
            self.__add_problem(pid, row['name'], row.rating, row.tags)
        self.db.commit()
        
    def __add_problem(self, pid, name, rating, tags):
        tags_json = json.dumps(tags)
        sql = f'INSERT INTO problems  VALUES (?, ?, ?, ?);'
        self.db.execute(sql, (pid, name, rating, tags_json))

    def __all_pids(self):
        res = self.db.execute('SELECT pid FROM problems;')
        return set(pid[0] for pid in res)
        

class HistoryDB(DBTable):
    def __init__(self):
        super().__init__('history')

    def initialize(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS history ("
                "user TEXT NOT NULL, "
                "pid TEXT NOT NULL, "
                "action TEXT NOT NULL, "
                "timestamp DATETIME, "
                "CONSTRAINT check_t_action CHECK (action IN ('start', 'solve', 'giveup', 'timeout'))"
            ");"
        )
        self.db.commit()

    def last_action(self, username):
        res = self.db.execute(
                "SELECT * FROM history WHERE user=? ORDER BY ROWID DESC LIMIT 1;", (username, ))
        if not res:
            return None
        return pd.DataFrame(res, columns=('user pid action timestamp'.split())).iloc[0]

    def add_action(self, username, pid, action):
        last = self.last_action(username)
        if last is not None and last.action == 'start':
            assert last.pid == pid, 'consistency check failed!'
            assert action in ['solve', 'giveup', 'timeout'], 'consistency check failed!'
        if action in ['solve', 'giveup', 'timeout']:
            assert last is None or (last.pid == pid and last.action == 'start')
        self.db.execute(
            'INSERT INTO history VALUES (?, ?, ?, ?)',
            (username, pid, action, datetime.now())
        )
        self.db.commit()
        
    def get_history(self, username: str) -> pd.DataFrame:
        res = self.db.execute(
            f'SELECT * FROM history WHERE user="{username}" ORDER BY timestamp ASC')
        return pd.DataFrame(res, columns='user pid action timestamp'.split())

    def del_user(self, username: str):
        self.db.execute(f'DELETE FROM history WHERE user="{username}"')
        self.db.commit()


class SubmissionDB(DBTable):
    def __init__(self):
        super().__init__('submissions')

    def initialize(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS submissions ("
                "submission_id INTEGER PRIMARY KEY, "
                "user TEXT NOT NULL, "
                "pid TEXT NOT NULL, "
                "verdict TEXT NOT NULL"
            ");"
        )
        self.db.commit()

    def update(self, username):
        logger.info('updating your submission history')
        for submission_json in cf_get_submissions(username):
            sid = submission_json['id']
            verdict = submission_json['verdict']
            problem_json = submission_json['problem']
            pid = f'{problem_json["contestId"]}/{problem_json["index"].upper()}'
            try:
                self.db.execute(
                    'INSERT INTO submissions VALUES (?, ?, ?, ?)',
                    (sid, username, pid, verdict),
                )
            except sqlite3.IntegrityError:
                break
        self.db.commit()

    def check_solved(self, username, pid):
        res = self.db.execute(
            'SELECT COUNT(1) FROM submissions WHERE '
            'user=? AND pid=? AND verdict="OK"',
            (username, pid)
        )
        return res[0][0] > 0

    def all_solved(self, username):
        res = self.db.execute(
            'SELECT pid FROM submissions WHERE '
            'user=? AND verdict="OK"',
            (username, )
        )
        return [row[0] for row in res]


