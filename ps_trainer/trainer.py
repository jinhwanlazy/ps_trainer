import sys, select
import time
import logging
logger = logging.getLogger(__name__)

from .utils import input_char


def check_unfinished_session(user, hdb):
    last = hdb.last_action(user.name)
    if last is None or last.action != 'start':
        return None
    logger.info(f'unfinished session found! - pid: {last.pid}, timestamps: {last.timestamp}')
    return last
    

def select_problem(user, pdb, sdb, rating_range=200):
    # TODO do this with single sql query.
    solved_pids = sdb.all_solved(user.name)
    for _ in range(100):
        min_rating = user.rating.rating - rating_range
        max_rating = user.rating.rating + rating_range
        problems = pdb.get_problems_with_rating_range(min_rating, max_rating)
        problems = problems[~problems.pid.isin(solved_pids)]
        if len(problems) > 0:
            p = problems.sample(n=1).iloc[0]
            logger.debug(f'selected a problem - pid: {p.pid}, rating: {p.rating}')
            return p
        logger.info(f'no problems in range {min_rating} - {max_rating}, increase range and try again..')
        rating_range += 100
    logger.warning(f'failed to find problem to solve. may you solved all problems in codeforce?')
    return None


def check_solved(user, problem, sdb):
    sdb.update(user.name)
    return sdb.check_solved(user.name, problem.pid)


def start_session(user, problem, sdb, timeout=3600, message='', show_problem_rating=True):
    start_time = time.time()
    # prompt = [message] if message else []
    prompt = []
    prompt.append(f'Problem      : {problem.pid.replace("/", "")} - {problem["name"]}')
    if show_problem_rating:
        prompt.append(f'Rating       : {int(problem.rating)}')
    prompt.append(f'URL          : https://codeforces.com/problemset/problem/{problem.pid}')
    prompt.append( 'RemainingTime: {remaining_min:02d}:{remaining_sec:.1f}')
    prompt.append( 'Message      : {message}')
    prompt.append('\n[s]olved, [g]iveup, [q]uit\n')
    prompt = '\n'.join(prompt)

    while True:
        remaining_time = timeout - (time.time() - start_time)
        remaining_min = int(remaining_time) // 60
        remaining_sec = remaining_time % 60 
        if remaining_time <= 0:
            break
        char = input_char(message=prompt.format(**locals()), timeout=0.10)
        if char is None:
            continue
        logger.debug(f'user input! - {char}')
        if char.lower() in 's':
            if check_solved(user, problem, sdb):
                logger.info('congrats you solved the problem!')
                logger.debug('solved')
                return 'solve'
            else:
                message = "make sure you solved the problem"
                continue
        if char.lower() in 'g':
            logger.info('you gave up the session!')
            return 'giveup'
        if char.lower() in 'q':
            logger.info('quited session. it will automatically resumed when you start new session')
            return 'quit'
        message = f'"{char}" is not valid input!'

    if check_solved(user, problem, sdb):
        logger.info('congrats you solved the problem!')
        logger.debug('solved')
        return 'solve'
    else:
        logger.info('session timed out!')
        return 'timeout'

