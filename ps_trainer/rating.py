from typing import List, Optional
from datetime import datetime

DEFAULT_RATING = 1400

class Rating:
    def __init__(self, start_rating=DEFAULT_RATING, count_step=0, count_solve=0):
        self.rating = start_rating
        self.count_step = count_step
        self.count_solve = count_solve

    def step(self, problem_rating: float, solved: bool) -> float:
        self.count_step += 1
        self.count_solve += int(solved)
        return self._step(problem_rating, solved)

    def _step(self, problem_rating: float, solved: bool) -> float:
        raise NotImplementedError

    @staticmethod
    def prob_solve(rating: float, problem_rating: float) -> float:
        return 1.0 / (1 + 10**((problem_rating - rating) / 400))

    def __repr__(self):
        return f'{int(self.rating)}, solved: {self.count_solve}, attempt: {self.count_step}'


class ELO(Rating):
    def __init__(self, start_rating=DEFAULT_RATING, count_step=0, count_solve=0, K=24):
        super().__init__(start_rating, count_step, count_solve)
        self.K = K

    def _step(self, problem_rating, solved):
        p = Rating.prob_solve(self.rating, problem_rating)
        self.rating = self.rating + self.K * (float(solved) - p)
        return self.rating

