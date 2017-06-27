"""Definition of various common objects.

"""

from collections import namedtuple


TEST_TYPES = {'hidden', 'public', 'community'}
TestResult = namedtuple('TestResult', 'name type succeed')


class SubmissionResult():
    """Object created by the server and returned to the player"""

    def __init__(self, tests, full_trace, problem_id):
        self._tests = dict(tests)
        self._full_trace = str(full_trace)
        self._problem_id = int(problem_id)
        self._total_success = all(test.succeed for test in tests.values())

    @property
    def total_success(self): return self._total_success
    @property
    def tests(self): return self._tests
    @property
    def full_trace(self): return self._full_trace
    @property
    def problem_id(self): return self._problem_id
    @property
    def total_success(self): return self._total_success
