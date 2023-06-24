import os, stat
import time
import logging
logger = logging.getLogger(__name__)

import requests
import curses
import pandas as pd

from . import __datadir__

def file_age(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]


def input_char(message, timeout=0):
    try:
        win = curses.initscr()
        win.addstr(0, 0, message)
        if timeout > 0:
            win.timeout(int(timeout * 1000))
        ch = win.getch()
        if ch not in range(32, 127): 
            return None
    finally:
        curses.endwin()
    return chr(ch)


def read_confirm(msg):
    while True:
        res = input_char(msg + '\nAre you sure? [y/N]')
        if res.lower() == 'y':
            return True
        elif res.lower() == 'n':
            return False


def cf_get_all_problems():
    cache_filepath = os.path.join(__datadir__, 'problems.pkl')
    if os.path.isfile(cache_filepath) and file_age(cache_filepath) < 3600:
        logger.debug("skipping update problem list")
        return None
        
    api_url = 'https://codeforces.com/api/problemset.problems'
    logger.debug(f'load problem list from {api_url}')
    res = requests.get(url=api_url).json()['result']['problems']
    df = pd.DataFrame(res)
    df.to_pickle(cache_filepath)
    return df


def cf_get_submissions(handle):
    start = 1
    count = 100
    request_interval = 4
    while True:
        api_url = f'https://codeforces.com/api/user.status?handle={handle}&from={start}&count={count}'
        logger.debug(f'requesting submission list from {api_url}')
        res = requests.get(url=api_url)
        if not res.ok:
            logger.warning(f'failed to get submissions - {res.text}')
            break
        res = res.json()['result']
        if not res:
            break
        for submission_json in res:
            yield submission_json
        start += count
        time.sleep(request_interval)

