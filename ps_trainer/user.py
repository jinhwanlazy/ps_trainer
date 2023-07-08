import pandas as pd

from .rating import ELO
from .config import save_config
from collections import defaultdict

class User:
    def __init__(self, name):
        self.name = name
        self.rating = ELO()
        self.tag_ratings = defaultdict(ELO)

    def update(self, problem, solved):
        self.__update([solved], [problem])

    def initialize(self, pdb, hdb):
        pids_seen = set()
        pids, outcomes = [], []
        prev = None
        for i, hist in hdb.get_history(self.name).iterrows():
            if prev is None:
                prev = hist
                continue
            if prev.pid == hist.pid and prev.action == 'start' and hist.pid not in pids_seen:
                assert hist.action != 'start'
                pids_seen.add(hist.pid)
                pids.append(hist.pid)
                outcomes.append(hist.action == 'solve')
            prev = hist
        problems = pdb.get_problems_with_pids(pids)
        self.__update(outcomes, problems)

    def __update(self, list_solved, problems):
        if isinstance(problems, pd.DataFrame):
            problems = problems.iterrows()
        elif isinstance(problems, list):
            problems = enumerate(problems)
        for solved, (i, problem) in zip(list_solved, problems):
            self.rating.step(problem.rating, solved)
            for tag in problem.tags:
                self.tag_ratings[tag].step(problem.rating, solved)

    def __repr__(self):
        def to_dict(tag, rating):
            return {
                'tag': tag, 
                'rating': int(rating.rating),
                'solved': rating.count_solve,
                'attempt': rating.count_step,
            }
        if not self.tag_ratings:
            return f"{self.name} you haven't solved a problem yet"
        df = pd.DataFrame((to_dict(tag, rating) for tag, rating in self.tag_ratings.items()))
        df.sort_values(by=['rating'], ascending=False, ignore_index=False, inplace=True)
        df.loc[len(df)] = to_dict('-- Total --', self.rating)
        return f'{self.name}\n' + df.to_string(index=False)


def assert_valid_username(name):
    assert isinstance(name, str), f"invalid username - {name}"
    assert len(name) > 0, f"invalid username - {name}"


def get_current_user(cfg):
    if cfg.USERNAME:
        return User(cfg.USERNAME)

    new_username = input('enter your codeforces handle: ')
    assert_valid_username(new_username)

    cfg.USERNAME = new_username
    save_config()
    return User(new_username)


