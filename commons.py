"""Definition of various common objects.

"""

import json
from collections import namedtuple


TEST_TYPES = {'hidden', 'public', 'community'}
TestResult = namedtuple('TestResult', 'name type succeed')


class ServerError(Exception):
    """Raised by Server when players are using the service badly"""
    pass


def custom_json_encoder(cls:type or [type]) -> json.JSONEncoder:
    """Return a class ready to be used by json module to encode given
    class(es) of custom objects.

    Classes must provide a as_json() method returning json serializable data.

    See https://docs.python.org/3.6/library/json.html for more background.

    """
    class CustomObjectEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, cls):
                return obj.to_json()
            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)
    return CustomObjectEncoder

def custom_json_decoder(classes:[type]):
    def custom_object_decoder(dct):
        for cls in classes:
            interp = cls.from_json(dct)
            if interp:
                return interp
        # nothing found
        return dct
    return custom_object_decoder



class SubmissionResult:
    """Object created by the server and returned to the player"""
    __slots__ = ['_tests', '_full_trace', '_problem_id', '_source_code']

    def __init__(self, tests:iter, full_trace:str, problem_id, source_code:str):
        self._tests = tuple(tests)
        self._full_trace = str(full_trace)
        self._problem_id = int(problem_id)
        self._source_code = str(source_code)

    @property
    def tests(self): return self._tests
    @property
    def full_trace(self): return self._full_trace
    @property
    def problem_id(self): return self._problem_id
    @property
    def source_code(self): return self._source_code
    @property
    def total_success(self): return all(test.succeed for test in self.tests)

    @property
    def fields(self) -> iter:
        yield from (field.lstrip('_') for field in self.__slots__)


    def to_json(self) -> dict:
        return {'__weldon_SubmissionResult__': {
            field: getattr(self, field)
            for field in self.fields
        }}

    @staticmethod
    def from_json(data:dict) -> object:
        payload = data.get('__weldon_SubmissionResult__')
        if payload:
            return SubmissionResult(**payload)
