import shutil
from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)

from .user import get_current_user
from .db import ProblemDB, HistoryDB, SubmissionDB
from .config import Config
from .utils import read_confirm
from . import trainer
from . import __logdir__, __datadir__

def start():
    logger.debug('start() called')
    config = Config()
    hdb = HistoryDB()
    pdb = ProblemDB()
    sdb = SubmissionDB()
    user = get_current_user(config)
    user.initialize(pdb, hdb)
    sdb.update(user.name)

    last = trainer.check_unfinished_session(user, hdb)
    remaining_time = 0
    if last is not None:
        logger.info(f'unfinished problem exist - {last.pid}')
        remaining_time = config.time_limit - (datetime.now() - last.timestamp).seconds
        if remaining_time <= 0:
            logger.info('unfinished problem marked as timeout')
            hdb.add_action(user.name, last.pid, 'timeout')
        else:
            problem = pdb.get_problem(last.pid)

    if remaining_time > 0:
        logger.info('resuming last session')
        problem = pdb.get_problem(last.pid)
        message = 'Resumed from your last session'
    else:
        remaining_time = config.time_limit
        problem = trainer.select_problem(user, pdb, sdb)
        logger.info(f'selected new problem - {problem.pid}')
        message = ''
        hdb.add_action(user.name, problem.pid, 'start')

    result = trainer.start_session(user, problem, sdb, remaining_time, message)
    if result in ['solve', 'giveup', 'timeout']:
        rating_before = user.rating.rating
        hdb.add_action(user.name, problem.pid, result)
        user.update(problem, result == 'solve')
        rating_after = user.rating.rating
        logger.info(f'rating updated: {int(rating_before)} -> {int(rating_after)}')
    

def print_status():
    logger.debug('print_status() called')
    config = Config()
    hdb = HistoryDB()
    pdb = ProblemDB()
    user = get_current_user(config)
    user.initialize(pdb, hdb)
    print(user)

def print_history():
    logger.debug('print_history() called')
    config = Config()
    hdb = HistoryDB()
    user = get_current_user(config)
    print(hdb.get_history(user.name))

def reset():
    logger.debug('reset called')
    if read_confirm(f'All your progress will be lost.'):
        logger.warning(f'removing {__logdir__}')
        shutil.rmtree(__logdir__)
        logger.warning(f'removing {__datadir__}')
        shutil.rmtree(__datadir__)
    else:
        logger.debug('reset canceled')


def get_command_list():
    return {
        'start': start,
        'status': print_status,
        'history': print_history,
        'reset': reset,
    }
