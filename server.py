"""Definition of the weldon Server class.

"""


import os
import re
import uuid
from collections import defaultdict, namedtuple

from commons import SubmissionResult
from problem import Problem
from run_pytest import (run_tests_on_problem,
                        extract_results_from_pytest_output)


class Server:
    """Object that host problems and receive and test submissions"""

    def __init__(self, player_password='', rooter_password=''):
        self.problems = {}  # id or name: Problem instance
        self._next_problem_id = 1
        self.rooter_password = str(rooter_password)
        self.player_password = str(player_password)
        self.tokens_player = set()
        self.tokens_rooter = set()
        self.restricted_to_rooter = {self.register_problem, self.retrieve_problem,
                                     self.add_hidden_test, self.add_public_test}
        self._db = defaultdict(lambda: defaultdict(list))  # token: {problem_id: [data]}
        self._players_name = {}  # token: name

    def register_player(self, name:str, password:str='') -> str:
        if password == self.player_password:
            new = str(uuid.uuid4())
            self.tokens_player.add(new)
            self._players_name[new] = str(l for l in name if re.match(r'[a-zA-Z_0-9]', l))
            return new

    def register_rooter(self, password:str='') -> str:
        if password == self.rooter_password:
            new = str(uuid.uuid4())
            self.tokens_rooter.add(new)
            return new

    def register_problem(self, token:str, title:str, description:str,
                         public_tests:str, hidden_tests:str) -> id:
        """Register a new problem with given description and tests"""
        self.validate_token(token, self.register_problem)
        problem = Problem(self._yield_problem_id(), title, description,
                          public_tests, hidden_tests, author=token)
        self.problems[problem.id] = problem
        self.problems[problem.title] = problem
        return problem.as_public_data()

    def _get_problem(self, problem_id:Problem or int or str) -> Problem or ValueError:
        """Access to a problem knowing its id or title"""
        if isinstance(problem_id, Problem):
            problem_id = problem.id
        problem = self.problems.get(problem_id)
        if not problem:
            raise ValueError("Problem {} do not exists".format(problem_id))
        return problem

    def retrieve_problem(self, token:str, problem_id:int or str) -> Problem or ValueError:
        """Return problem of given id or name ; raise ValueError if no problem"""
        self.validate_token(token, self.retrieve_problem)
        return self._get_problem(problem_id)

    def retrieve_public_problem(self, token:str, problem_id:str) -> Problem or ValueError:
        """If token is allowed to, return the public version of wanted problem"""
        self.validate_token(token, self.retrieve_public_problem)
        return self._get_problem(problem_id).as_public_data()

    def _yield_problem_id(self):
        """Yield a new unused problem id"""
        self._next_problem_id += 1
        return self._next_problem_id - 1

    def submit_solution(self, token:str, problem_id:int, source_code:str) -> ValueError or SubmissionResult:
        """Run unit tests for given problem using given solution.

        token -- unique token of the player
        problem_id -- uid of a problem known by Server instance
        source_code -- the file containing the code implementing the solution

        Raise ValueError if problem_id is not valid, or a SubmissionResult object.

        """
        self.validate_token(token, self.submit_solution)
        return self._run_tests_for_player(token, problem_id, source_code)


    def submit_test(self, token:str, problem_id:int, test_code:str) -> ValueError or None:
        """
        """
        self.validate_token(token, self.submit_test)
        problem = self._get_problem(problem_id)
        if not self._test_upload_allowed(token, problem_id):
            raise ValueError("Given token's last submission did not succeed all tests")

        # verify that player succeeds on this new test
        alt_problem = problem.copy()
        alt_problem.add_community_test(str(test_code))
        source_code = self._player_last_submission(token, problem_id).source_code
        submission_result = self._run_tests_for_player(token, alt_problem, source_code, dry=True)
        if not submission_result.total_success:
            raise ValueError("Given test fail on last submission")
        # player provide a test he pass himself, so it can be added to the tests
        problem.add_community_test(str(test_code))


    def add_public_test(self, token:str, problem_id:int, test_code:str) -> ValueError or None:
        """Add given test to the set of public tests of given problem"""
        self.validate_token(token, self.add_public_test)
        problem = self._get_problem(problem_id)
        problem.add_public_test(str(test_code))

    def add_hidden_test(self, token:str, problem_id:int, test_code:str) -> ValueError or None:
        """Add given test to the set of hidden tests of given problem"""
        self.validate_token(token, self.add_hidden_test)
        problem = self._get_problem(problem_id)
        problem.add_hidden_test(str(test_code))


    def _test_upload_allowed(self, token:str, problem_id:int) -> bool:
        if self._player_succeed_all_tests(token, problem_id):
            return True
        if token in self._testers:
            return True
        return False


    def validate_token(self, token:str, method:callable) -> ValueError or None:
        """Raise an error if given token do not have access to given method"""
        rooter = token in self.tokens_rooter
        player = token in self.tokens_player
        need_rooter = method in self.restricted_to_rooter
        if not rooter and not player:
            raise ValueError("Given token is not allowed to do anything.")
        if not rooter and need_rooter:
            error_msg = lambda func: func
            raise ValueError("Given token is not allowed to {}"
                             "".format(method.__name__.replace('_', ' ')))


    def _update_player_state(self, token:str, source_code:str, result:SubmissionResult):
        """Update internal database on players about player of given token
        and given submission result.

        """
        Entry = namedtuple('Entry', 'source_code result')
        self._db[token][result.problem_id].append(Entry(source_code, result))

    def _player_last_submission(self, token:str, problem_id:str) -> (str, str) or None:
        """Return last player source code and results for given problem"""
        try:
            return self._db[token][problem_id][-1]
        except IndexError:
            return None

    def _player_succeed_all_tests(self, token:str, problem_id:str) -> bool:
        """True if player of given token has succeed for all tests"""
        last_sub = self._player_last_submission(token, problem_id)
        if not last_sub: return False  # no submission
        last_result = last_sub.result
        return all(test.succeed for test in last_result.tests.values())

    def _run_tests_for_player(self, token:str, problem_id:int, source_code:str,
                              *, dry=False) -> SubmissionResult:
        """Perform the testing of player of given token on unit tests of
        given problem using the player source code.

        dry -- do not write results in database. Just run the tests.

        """
        problem = self._get_problem(problem_id)
        problem_id = problem.id
        test_result = run_tests_on_problem(problem, source_code)
        result = extract_results_from_pytest_output(test_result, problem_id)
        if not dry:
            self._update_player_state(token, source_code, result)
        return result
