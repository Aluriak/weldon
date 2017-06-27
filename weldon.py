"""Basic implementation of the weldon system.

"""


import os
import re
import uuid
import shutil
import subprocess
from collections import defaultdict

import pytest

from collections import namedtuple


TEST_TYPES = {'hidden', 'public', 'community'}
SubmissionResult = namedtuple('SubmissionResult', 'tests full_trace problem_id')
TestResult = namedtuple('TestResult', 'name type succeed')


class Problem:
    """Definition of a problem"""

    def __init__(self, id:int, title:str, description:str, public_tests:str,
                 hidden_tests:str, source_name:str=None, author:str=None,
                 community_tests:str=''):
        self._id = int(id)
        self._title = str(title)
        self._description = str(description)
        self._public_tests = str(public_tests)
        self._hidden_tests = str(hidden_tests)
        self._community_tests = str(community_tests)
        self._source_name = str(source_name or 'problem{}'.format(self.id))
        self._author = str(author or 'unknow')

    @property
    def id(self): return self._id
    @property
    def title(self): return self._title
    @property
    def description(self): return self._description
    @property
    def public_tests(self): return self._public_tests
    @property
    def hidden_tests(self): return self._hidden_tests
    @property
    def community_tests(self): return self._community_tests
    @community_tests.setter
    def community_tests(self, tests:str): self._community_tests = str(tests)
    @property
    def author(self): return self._author
    @property
    def source_name(self): return self._source_name

    def source_code_filename(self, dir:str='.') -> str:
        return os.path.join(dir, self.source_name + '.py')
    def public_test_filename(self, dir:str) -> str:
        return os.path.join(dir, 'test_public_cases.py')
    def hidden_test_filename(self, dir:str) -> str:
        return os.path.join(dir, 'test_hidden_cases.py')
    def community_test_filename(self, dir:str) -> str:
        return os.path.join(dir, 'test_community_cases.py')

    def as_public_data(self):
        """Return the very same object, but without the hidden unit tests"""
        return Problem(self.id, self.title, self.description, self.public_tests,
                       '', self.source_name, self.author, self.community_tests)


class Server:
    """Object that host problems and receive and test submissions"""

    def __init__(self, player_password='', rooter_password=''):
        self.problems = {}  # id or name: Problem instance
        self._next_problem_id = 1
        self.rooter_password = str(rooter_password)
        self.player_password = str(player_password)
        self.tokens_player = set()
        self.tokens_rooter = set()
        self.restricted_to_rooter = {self.register_problem, self.retrieve_problem}
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
        if not self._player_succeed_all_tests(token, problem_id):
            raise ValueError("Given token's last submission did not succeed all tests")
        problem.community_tests += '\n' + str(test_code)


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

    def _run_tests_for_player(self, token:str, problem_id:int, source_code:str) -> SubmissionResult:
        problem = self._get_problem(problem_id)
        test_result = run_tests_on_problem(problem, source_code)
        result = extract_results_from_pytest_output(test_result, problem_id)
        self._update_player_state(token, source_code, result)
        return result





def run_tests_on_problem_by_fixture(problem, source_code, run_dir='./run/'):
    """Run problem specs on given source code, in given run_dir.

    This method is interesting, but needs to be ran by pytest itself.
    So it can't be used inside the server implementation…
    """
    TEMPLATE_TEST_UNIT = """
    import pytest
    pytest_plugins = "pytester"

    def test_something(testdir):
        "Test some thing."
        testdir.makepyfile('''{}''')
        result = testdir.runpytest('-vv')
        import re
        for line in result.stdout.lines:
            match = re.match(r'[a-zA-Z_0-9]+\.py::(test_[a-zA-Z_0-9]+) ([PASSEDFAIL]+)', line)
            if match:
                testname, result = match.groups()
                assert result == 'PASSED', "Test {} did not succeed".format(testname)
    """
    TEST_FILE = os.path.join(run_dir, 'test_all.py')
    with open(TEST_FILE, 'w') as fd:
        fd.write(TEMPLATE_TEST_UNIT.format(
            'import pytest\n'
            + 'from {} import *\n\n'.format(problem.source_name)
            + problem.public_tests
            + problem.hidden_tests
        ))

    # todo: intercept and return stdout
    pytest.main([TEST_FILE], ['pytester'])


def run_tests_on_problem_by_main(problem, source_code, run_dir='./run/'):
    """Run problem specs on given source code, in given run_dir

    This method is interesting, but pytest print results in stdout.
    This is a way to go, but needs interception of stdout.

    Another way, maybe the most simple, could be to call the pytest binary
    via subprocess. This way, later implementations with protection
    about executed code (apparmor for instance) could easily be plugged.
    """
    runnable_source_code_file = problem.source_code_filename(dir=run_dir)
    runnable_public_test_file = problem.public_test_filename(dir=run_dir)
    runnable_hidden_test_file = problem.hidden_test_filename(dir=run_dir)
    with open(runnable_source_code_file, 'w') as fd:
        fd.write(source_code)
    with open(runnable_public_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.public_tests)
    with open(runnable_hidden_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.hidden_tests)

    # todo: intercept and return stdout
    pytest.main([run_dir])


def run_tests_on_problem_by_subprocess(problem, source_code, run_dir='./run/',
                                       test_output:str='./run/test_output'):
    """Run problem specs on given source code, in given run_dir.

    WARNING: Will erase everything found in run_dir.

    Return the tests results (raw lines returned by pytest).

    This method is interesting, but go out of python.
    Could be an advantage when passing by apparmor or other sandboxing modes.
    """
    # first backup and empty the run dir
    backup_dir = run_dir.rstrip('/') + '.backup'
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    if os.path.exists(run_dir):
        shutil.move(run_dir, backup_dir)
    os.mkdir(run_dir)

    # populate the run dir
    runnable_source_code_file = problem.source_code_filename(dir=run_dir)
    runnable_public_test_file = problem.public_test_filename(dir=run_dir)
    runnable_hidden_test_file = problem.hidden_test_filename(dir=run_dir)
    runnable_community_test_file = problem.community_test_filename(dir=run_dir)
    with open(runnable_source_code_file, 'w') as fd:
        fd.write(source_code)
    with open(runnable_public_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.public_tests)
    with open(runnable_hidden_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.hidden_tests)
    with open(runnable_community_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.community_tests)
    # run the tests
    proc = subprocess.Popen(['pytest', run_dir, '-vv'], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return stdout.decode()


run_tests_on_problem = run_tests_on_problem_by_main
run_tests_on_problem = run_tests_on_problem_by_fixture
run_tests_on_problem = run_tests_on_problem_by_subprocess


def extract_results_from_pytest_output(output:str, problem_id:str) -> SubmissionResult:
    """Return a SubmissionResult instance describing given pytest output"""
    reg_test = re.compile(r'^[\/a-zA-Z_0-9]+test_([hiddenpubliccommunity]+)_cases\.py::test_([a-zA-Z_0-9]+) ([PASSEDFAIL]+)$')
    TestResult
    tests = {}  # test name: test status
    for line in output.splitlines(keepends=False):
        match = reg_test.match(line)
        if match:
            type, testname, result = match.groups()
            assert type in TEST_TYPES
            tests[testname] = TestResult(testname, type, result == 'PASSED')
    return SubmissionResult(tests=tests, full_trace=str(output), problem_id=problem_id)


def submit_solution(server, problem, source_code):
    pass
