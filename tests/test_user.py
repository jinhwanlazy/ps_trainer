import time

from ps_trainer.db import ProblemDB, HistoryDB
from ps_trainer.user import User

from pytest import approx

def test_user():
    pdb = ProblemDB()

    user = User('DUMMY_USERNAME')
    user.update(pdb.get_problem('1/C'), False)
    user.update(pdb.get_problem('1/B'), True)
    user.update(pdb.get_problem('1/A'), True)

    assert user.rating.count_step == 3
    assert user.rating.count_solve == 2
    assert approx(user.rating.rating) == 1419.8118

    assert user.tag_ratings['geometry'].count_step == 1
    assert user.tag_ratings['math'].count_step == 3
    assert user.tag_ratings['implementation'].count_step == 1

    assert user.tag_ratings['geometry'].count_solve == 0
    assert user.tag_ratings['math'].count_solve == 2
    assert user.tag_ratings['implementation'].count_solve == 1

    assert approx(user.tag_ratings['geometry'].rating) == 1399.5807
    assert approx(user.tag_ratings['math'].rating) == 1419.8118
    assert approx(user.tag_ratings['implementation'].rating) == 1418.2339

