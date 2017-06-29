"""Definition of the weldon Server class.

"""


import os
import re
import uuid
from collections import defaultdict, namedtuple

from wtest import Test
from commons import SubmissionResult, ServerError
from problem import Problem
from run_pytest import result_from_pytest
from player_report import make_report_on_player


# A valider is a pair (valider function, error message)
DEFAULT_VALIDER = (lambda _: True, "Default valider is bugged")  # always ok by default
NAME_MAIL_VALIDER = (
    lambda x: bool(re.fullmatch(r'[a-zA-Z0-9\.-]+@[a-zA-Z0-9\.-]+\.[a-z]+', x)),
    "Name must be an email adress ; Note that the regex for mail address "
    "detection is probably not exhaustive"
)


class Server:
    """Object that host problems and receive and test submissions"""

    def __init__(self, player_password='', rooter_password='',
                 player_name_valider:(callable, str)=DEFAULT_VALIDER,
                 rooter_name_valider:(callable, str)=DEFAULT_VALIDER):
        """
        password -- the password expected to register.
        name_valider -- map name to boolean. If true, registration is accepted.

        The name valider is here to enforce players or rooters to adopt a
        particular naming scheme, that could be anything, like an email adress
        (see NAME_MAIL_VALIDER for this particular case).

        """
        self._player_name_valider = player_name_valider
        self._rooter_name_valider = rooter_name_valider
        self.problems = {}  # id or name: Problem instance
        self.open_problems = set()  # id of problems workable by students
        self._next_problem_id = 1
        self.rooter_password = str(rooter_password)
        self.player_password = str(player_password)
        self.tokens_player = set()
        self.tokens_rooter = set()
        self.restricted_to_rooter = {self.register_problem, self.retrieve_problem,
                                     self.add_hidden_test, self.add_public_test,
                                     self.close_problem_session,
                                     self.retrieve_players_of}
        self._db = defaultdict(lambda: defaultdict(list))  # token: {problem_id: [data]}
        self._players_name = {}  # token: name

    def register_player(self, name:str, password:str='') -> str:
        if password == self.player_password:
            valider, err = self._player_name_valider
            if not valider(name):
                raise ServerError('Bad name: ' + str(err))
            new = str(uuid.uuid4())
            self.tokens_player.add(new)
            self._players_name[new] = str(name)
            return new
        else:
            raise ServerError('Registration failed: bad password.')

    def register_rooter(self, name:str, password:str='') -> str:
        if password == self.rooter_password:
            new = str(uuid.uuid4())
            self.tokens_rooter.add(new)
            self._players_name[new] = str(l for l in name if re.match(r'[a-zA-Z_0-9]', l))
            return new

    def register_problem(self, token:str, title:str, description:str,
                         public_tests:str, hidden_tests:str) -> id:
        """Register a new problem with given description and tests,
        and open its session.

        """
        self.validate_token(token, self.register_problem)
        problem = Problem(self._yield_problem_id(), title, description,
                          public_tests, hidden_tests, author=token)
        self.problems[problem.id] = problem
        self.problems[problem.title] = problem
        self.open_problems.add(problem.id)
        return problem.as_public_data()

    def _get_problem(self, problem_id:Problem or int or str) -> Problem or ServerError:
        """Access to a problem knowing its instance or id or title."""
        if isinstance(problem_id, Problem):
            # return the given instance, not the instance known by server
            if problem_id.id in self.problems:
                return problem_id
            else:
                problem_id = problem_id.id
        problem = self.problems.get(problem_id)
        if not problem:
            raise ServerError("Problem {} do not exists".format(problem_id))
        return problem

    def retrieve_problem(self, token:str, problem_id:int or str) -> Problem or ServerError:
        """Return problem of given id or name ; raise ServerError if no problem"""
        self.validate_token(token, self.retrieve_problem)
        return self._get_problem(problem_id)

    def retrieve_public_problem(self, token:str, problem_id:str) -> Problem or ServerError:
        """If token is allowed to, return the public version of wanted problem"""
        self.validate_token(token, self.retrieve_public_problem)
        return self._get_problem(problem_id).as_public_data()

    def _yield_problem_id(self):
        """Yield a new unused problem id"""
        self._next_problem_id += 1
        return self._next_problem_id - 1

    def close_problem_session(self, token:str, problem_id:int or str) -> None or ServerError:
        """Remove given problem of the list of open problems"""
        self.validate_token(token, self.close_problem_session)
        problem = self._get_problem(problem_id)
        try:
            self.open_problems.remove(problem.id)
        except KeyError:  # problem not in open problems
            raise ServerError("Given problem ({}) is already closed".format(problem.title))


    def retrieve_report(self, token:str, problem_id:int or str) -> str or ServerError:
        """Return A full report about given token activity of given problem"""
        self.validate_token(token, self.retrieve_report)
        problem = self._get_problem(problem_id)
        player_name = self._players_name[token]
        report = make_report_on_player(player_name, self._player_submissions(token, problem.id))
        return '\n'.join(report)

    def retrieve_players_of(self, token:str, problem_id:int or str) -> [str] or ServerError:
        """Return tokens of players associated to given problem

        TODO: This is dangerous, since token can be sent by the server.
        An improved solution could be to allow internal mapping between
        players name and their token inside the server,
        and allow rooters to use players names
        instead of their tokens.
        This also need the Server to force players
        to use all different names.

        """
        self.validate_token(token, self.retrieve_players_of)
        problem = self._get_problem(problem_id)
        return tuple(self._players_involved_in(problem.id))


    def submit_solution(self, token:str, problem_id:int, source_code:str) -> ServerError or SubmissionResult:
        """Run unit tests for given problem using given solution.

        token -- unique token of the player
        problem_id -- uid of a problem known by Server instance
        source_code -- the file containing the code implementing the solution

        Raise ServerError if problem_id is not valid, or a SubmissionResult object.

        """
        self.validate_token(token, self.submit_solution)
        return self._run_tests_for_player(token, problem_id, source_code)


    def submit_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """
        """
        self.validate_token(token, self.submit_test)
        problem = self._get_problem(problem_id)
        self.validate_test(token, test_code, problem.id)
        problem.add_community_test(Test(str(test_code), token, 'community'))


    def validate_test(self, token:str, test_code, problem_id) -> ServerError or None:
        """Raise ServerError if anything goes wrong."""
        problem = self._get_problem(problem_id)
        if not self._test_upload_allowed(token, problem.id):
            raise ServerError("Given token's last submission did not succeed all tests")

        # verify that player succeeds on this new test
        alt_problem = problem.copy()
        alt_problem.add_community_test(Test(str(test_code), token, 'community'))
        source_code = self._player_last_submission(token, problem_id).source_code
        submission_result = self._run_tests_for_player(token, alt_problem, source_code, dry=True)
        if not submission_result.total_success:
            raise ServerError("Given test fail on last submission")


    def add_public_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """Add given test to the set of public tests of given problem"""
        self.validate_token(token, self.add_public_test)
        problem = self._get_problem(problem_id)
        problem.add_public_test(Test(str(test_code), token, 'public'))

    def add_hidden_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """Add given test to the set of hidden tests of given problem"""
        self.validate_token(token, self.add_hidden_test)
        problem = self._get_problem(problem_id)
        problem.add_hidden_test(Test(str(test_code), token, 'hidden'))


    def _test_upload_allowed(self, token:str, problem_id:int) -> bool:
        if self._player_succeed_all_tests(token, problem_id):
            return True
        if token in self._testers:
            return True
        return False


    def validate_token(self, token:str, method:callable) -> ServerError or None:
        """Raise an error if given token do not have access to given method"""
        rooter = token in self.tokens_rooter
        player = token in self.tokens_player
        need_rooter = method in self.restricted_to_rooter
        if not rooter and not player:
            raise ServerError("Given token ({}) is not allowed to do anything."
                             "".format(token))
        if not rooter and need_rooter:
            error_msg = lambda func: func
            raise ServerError("Given token is not allowed to {}"
                             "".format(method.__name__.replace('_', ' ')))


    def _update_player_state(self, token:str, source_code:str, result:SubmissionResult):
        """Update internal database on players about player of given token
        and given submission result.

        """
        self._db[token][result.problem_id].append(result)


    def _player_submissions(self, token:str, problem_id:str) -> [(str, str)]:
        """Return player sources code and results for given problem"""
        try:
            return tuple(self._db[token][problem_id])
        except IndexError:
            return ()

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
        return all(test.succeed for test in last_sub.tests.values())

    def _run_tests_for_player(self, token:str, problem_id:int, source_code:str,
                              *, dry=False) -> SubmissionResult:
        """Perform the testing of player of given token on unit tests of
        given problem using the player source code.

        dry -- do not write results in database. Just run the tests.

        """
        problem = self._get_problem(problem_id)
        problem_id = problem.id
        result = result_from_pytest(problem, source_code)
        if not dry:
            self._update_player_state(token, source_code, result)
        return result

    def _players_submit_solution_for(self, problem_id:str) -> iter:
        """Yield token of players that have submitted code to given problem."""
        problem_id = self._get_problem(problem_id).id
        yield from (
            token for token, problem_ids in self._db.items()
            if problem_id in problem_ids
        )

    def _players_submit_test_for(self, problem_id:str) -> iter:
        """Yield token of players that have submitted test to given problem."""
        problem = self._get_problem(problem_id)
        yield from (test.author for test in problem.community_tests)

    def _players_involved_in(self, problem_id:str) -> frozenset:
        """Return set of token of players that have participated to given problem,
        by submitting code or tests.
        """
        coders = self._players_submit_solution_for(problem_id)
        testers = self._players_submit_test_for(problem_id)
        return frozenset(coders) | frozenset(testers)
