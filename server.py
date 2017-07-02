"""Definition of the weldon Server class.

"""


import os
import re
import uuid
import inspect
import functools
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


def api_method(func:callable) -> callable:
    """Decorator around method callable by Server API.

    If decorated func have a `token` parameter, it will first be validated
    (by verifying it is valid for given operation)

    Also, functions wrapped will get a marker allowing server instances
    to know which functions belongs to the API.

    """
    formal_parameters = frozenset(inspect.signature(func).parameters.keys())
    have_token = 'token' in formal_parameters
    if 'token' in formal_parameters:
        # method is wrapped to automatically provide token validation
        @functools.wraps(func)
        def decorator(self, token, *args, **kwargs):
            self._validate_token(token, getattr(self, func.__name__))
            return func(self, token, *args, **kwargs)
    else:  # method is not wrapped (nothing to do)
        decorator = func
    decorator.belong_to_server_api = True  # marker
    return decorator


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
        self.problems = {}  # title: Problem instance
        self.problems_by_id = {}  # uid: Problem instance
        self.open_problems = set()  # id of problems workable by students
        self._next_problem_id = 1
        self.rooter_password = str(rooter_password)
        self.player_password = str(player_password)
        self.tokens_player = set()
        self.tokens_rooter = set()
        self.restricted_to_rooter = {self.register_problem,
                                     self.add_hidden_test, self.add_public_test,
                                     self.close_problem_session,
                                     self.retrieve_players_of}
        self._db = defaultdict(lambda: defaultdict(list))  # token: {problem_id: [data]}
        self._players_name = {}  # token: name


    # @property
    def api_methods(self) -> {str: bool}:
        """Return map of methods of server that belongs to the API with
        a boolean indicating if it needs root to be used.

        """
        return {
            func.__name__: func in self.restricted_to_rooter
            for _, func in inspect.getmembers(self, predicate=inspect.ismethod)
            if callable(func) and getattr(func, 'belong_to_server_api', False)
        }

    def api_methods_parameters(self) -> {str: (str,)}:
        """Return map of methods of server that belongs to the API with
        an iterable of the parameters name.

        """
        return {
            funcname: tuple(inspect.signature(getattr(self, funcname)).parameters.keys())
            for funcname in self.api_methods()
        }


    @api_method
    def get_api(self, token:str) -> {callable: {str,}}:
        """Return the available functions and their arguments as a dict.

        Will filter out reserved to root methods if caller is not one of them.

        """
        if token in self.tokens_rooter:
            return self.api_methods_parameters()
        return {name: params for name, params
                in self.api_methods_parameters().items()
                if not getattr(self, name) in self.restricted_to_rooter}

    def _register_user(self, name:str, password:str, root:bool=False) -> 'token' or ServerError:
        """Perform the registration for player (rooter if `root`)"""
        expected_password = self.rooter_password if root else self.player_password
        name_valider = self._rooter_name_valider if root else self._player_name_valider
        token_set = self.tokens_rooter if root else self.tokens_player
        if password == expected_password:
            valider, err = name_valider
            if not valider(name):
                raise ServerError('Bad name: ' + str(err))
            new = str(uuid.uuid4())
            token_set.add(new)
            self._players_name[new] = str(name)
            return new
        else:
            raise ServerError('Registration failed: bad password.')

    @api_method
    def register_player(self, name:str, password:str='') -> str:
        return self._register_user(name, password, root=False)

    @api_method
    def register_rooter(self, name:str, password:str='') -> str:
        return self._register_user(name, password, root=True)

    @api_method
    def list_problems(self, token:str) -> [id]:
        """Return all problem id available on this server"""
        return tuple(self.problems.keys())

    @api_method
    def register_problem(self, token:str, title:str, description:str,
                         public_tests:str, hidden_tests:str) -> id:
        """Register a new problem with given description and tests,
        and open its session.

        """
        if title in self.problems:
            author = self._players_name.get(self.problems[title].author, None)
            if self._players_name[token] == author:
                raise ServerError(f"You already submited a problem of title '{title}'")
            raise ServerError(f"{author} already submited a problem of title '{title}'")
        problem = Problem(self._yield_problem_id(), title, description,
                          public_tests, hidden_tests, author=token)
        self.problems_by_id[problem.id] = problem
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
        problem = self.problems_by_id.get(problem_id, self.problems.get(problem_id))
        if not problem:
            raise ServerError("Problem {} do not exists".format(problem_id))
        return problem

    @api_method
    def retrieve_problem(self, token:str, problem_id:int or str) -> Problem or ServerError:
        """Return problem of given id or name ; raise ServerError if no problem"""
        if token in self.tokens_rooter:
            return self._get_problem(problem_id)
        elif token in self.tokens_player:
            return self._get_problem(problem_id).as_public_data()

    @api_method
    def retrieve_public_problem(self, token:str, problem_id:str) -> Problem or ServerError:
        """If token is allowed to, return the public version of wanted problem"""
        return self._get_problem(problem_id).as_public_data()

    def _yield_problem_id(self):
        """Yield a new unused problem id"""
        self._next_problem_id += 1
        return self._next_problem_id - 1

    @api_method
    def close_problem_session(self, token:str, problem_id:int or str) -> None or ServerError:
        """Remove given problem of the list of open problems"""
        problem = self._get_problem(problem_id)
        try:
            self.open_problems.remove(problem.id)
        except KeyError:  # problem not in open problems
            raise ServerError("Given problem ({}) is already closed".format(problem.title))


    @api_method
    def retrieve_report(self, token:str, problem_id:int or str) -> str or ServerError:
        """Return A full report about given token activity of given problem"""
        problem = self._get_problem(problem_id)
        player_name = self._players_name[token]
        player_subs = self._player_submissions(token, problem.id)
        report = make_report_on_player(player_name, token, player_subs, problem)
        return '\n'.join(report)

    @api_method
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
        problem = self._get_problem(problem_id)
        return tuple(self._players_involved_in(problem.id))


    @api_method
    def submit_solution(self, token:str, problem_id:int, source_code:str) -> ServerError or SubmissionResult:
        """Run unit tests for given problem using given solution.

        token -- unique token of the player
        problem_id -- uid of a problem known by Server instance
        source_code -- the file containing the code implementing the solution

        Raise ServerError if problem_id is not valid, or a SubmissionResult object.

        """
        return self._run_tests_for_player(token, problem_id, source_code)


    @api_method
    def submit_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """
        """
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


    @api_method
    def add_public_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """Add given test to the set of public tests of given problem"""
        problem = self._get_problem(problem_id)
        problem.add_public_test(Test(str(test_code), token, 'public'))

    @api_method
    def add_hidden_test(self, token:str, problem_id:int, test_code:str) -> ServerError or None:
        """Add given test to the set of hidden tests of given problem"""
        problem = self._get_problem(problem_id)
        problem.add_hidden_test(Test(str(test_code), token, 'hidden'))


    def _test_upload_allowed(self, token:str, problem_id:int) -> bool:
        if self._player_succeed_all_tests(token, problem_id):
            return True
        if token in self._testers:
            return True
        return False


    def _validate_token(self, token:str, method:callable=None) -> ServerError or None:
        """Raise an error if given token do not have access to given method"""
        rooter = token in self.tokens_rooter
        player = token in self.tokens_player
        need_rooter = method in self.restricted_to_rooter
        if not rooter and not player:
            raise ServerError("Given token ({}) is not allowed to do anything."
                             "".format(token))
        if not rooter and need_rooter:
            error_msg = lambda func: func
            method_name = method.__name__.replace('_', ' ')
            raise ServerError("Given token is not allowed to {}"
                             "".format(method_name))


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
        return all(test.succeed for test in last_sub.tests)

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
