from ps_trainer.user import User
from ps_trainer.db import ProblemDB, HistoryDB, SubmissionDB
from ps_trainer.trainer import select_problem

def test_select_problem():
    pdb = ProblemDB()
    hdb = HistoryDB()
    sdb = SubmissionDB()
    user = User('jinhwanlazy')

    p = select_problem(user, pdb, sdb, 100)
    assert user.rating.rating - 100 <= p.rating <= user.rating.rating + 100
