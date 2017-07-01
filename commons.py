"""Definition of various common objects.

"""

from utils import jsonable_class


TEST_TYPES = {'hidden', 'public', 'community'}


class ServerError(Exception):
    """Raised by Server when players are using the service badly"""
    pass


TestResult = jsonable_class(
    'TestResult',
    ['_name', '_type', '_succeed'],
)

SubmissionResult = jsonable_class(
    'SubmissionResult',
    ['_tests', '_full_trace', '_problem_id', '_source_code'],
    other_attributes={
        'total_success': property(lambda self: all(test.succeed for test in self.tests))
    }
)
