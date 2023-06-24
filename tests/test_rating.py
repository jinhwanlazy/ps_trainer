from pytest import approx

from ps_trainer.rating import Rating, ELO, DEFAULT_RATING

def test_prob_est():
    assert approx(Rating.prob_solve(1000, 200)) == 100 / 101
    assert approx(Rating.prob_solve(1000, 600)) == 10 / 11
    assert approx(Rating.prob_solve(1000, 1000)) == 0.5
    assert approx(Rating.prob_solve(1000, 1400)) == 1 - 10 / 11
    assert approx(Rating.prob_solve(1000, 1800)) == 1 - 100 / 101

def test_elo():
    elo = ELO()
    assert elo.rating == DEFAULT_RATING
    assert elo.count_step == 0
    assert elo.count_solve == 0

    elo = ELO(1000)
    assert elo.rating == 1000

    assert ELO(1000).step(1000, 1) > 1000
    assert ELO(1000).step(1000, 0) < 1000
    assert ELO(1000).step(1000, 0) > ELO(1000).step(999, 0)
    assert ELO(1000).step(1000, 1) > ELO(1000).step(999, 1)
