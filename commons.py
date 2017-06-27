"""Definition of various common objects.

"""

from collections import namedtuple


TEST_TYPES = {'hidden', 'public', 'community'}
SubmissionResult = namedtuple('SubmissionResult', 'tests full_trace problem_id')
TestResult = namedtuple('TestResult', 'name type succeed')
