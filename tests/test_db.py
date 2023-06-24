import time
import pytest

from ps_trainer.db import ProblemDB, HistoryDB, SubmissionDB

def test_history_db():
    hdb = HistoryDB()

    username = 'DUMMY_USERNAME'

    hdb.del_user(username)
    last = hdb.last_action(username)
    assert last is None
    
    hdb.add_action(username, '1/A', 'start')
    last = hdb.last_action(username)
    assert last is not None

    with pytest.raises(Exception):
        hdb.add_action(username, '1/A', 'start')

    with pytest.raises(Exception):
        hdb.add_action(username, '1/A', 'INVALID_ACTION')

    with pytest.raises(Exception):
        hdb.add_action(username, '1/B', 'giveup')

    time.sleep(1)
    hdb.add_action(username, '1/A', 'solve')
    assert len(hdb.get_history(username)) == 2

    
def test_problem_db():
    pdb = ProblemDB()
    assert len(pdb) > 8000

    problem = pdb.get_problem('1/A')
    assert problem['name'] == 'Theatre Square'


def test_submission_db():
    sdb = SubmissionDB()
    
    username = 'jinhwanlazy' 
    sdb.update(username)

    assert sdb.check_solved(username, '1/A')
    assert not sdb.check_solved(username, 'NON_EXISTENT_PID')
