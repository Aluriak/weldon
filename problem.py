"""Problem class definition.

"""

import os
from test import Test


class Problem:
    """Definition of a problem, notabily description and unit tests"""
    __slots__ = ['_id', '_title', '_description', '_public_tests',
                 '_hidden_tests', '_community_tests',
                 '_source_name', '_author']

    def __init__(self, id:int, title:str, description:str, public_tests:iter,
                 hidden_tests:iter, source_name:str=None, author:str=None,
                 community_tests:iter=()):
        self._id = int(id)
        self._title = str(title)
        self._description = str(description)
        self._public_tests = Test.to_test_suite(public_tests)
        self._hidden_tests = Test.to_test_suite(hidden_tests)
        self._community_tests = Test.to_test_suite(community_tests)
        self._source_name = str(source_name or 'problem{}'.format(self.id))
        self._author = str(author or 'unknow')

    @property
    def id(self): return self._id
    @property
    def title(self): return self._title
    @property
    def description(self): return self._description
    @property
    def public_tests(self): return tuple(self._public_tests)
    @property
    def hidden_tests(self): return tuple(self._hidden_tests)
    @property
    def community_tests(self): return tuple(self._community_tests)
    @property
    def author(self): return self._author
    @property
    def source_name(self): return self._source_name

    @property
    def fields(self) -> iter:
        yield from (field.lstrip('_') for field in self.__slots__)


    def add_public_test(self, test:str):
        """Add a single test to public tests"""
        self._public_tests += (test,)
    def add_hidden_test(self, test:str):
        """Add a single test to hidden tests"""
        self._hidden_tests += (test,)
    def add_community_test(self, test:str):
        """Add a single test to community tests"""
        self._community_tests += (test,)


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
    def copy(self, id=None):
        """Return the very same object (eventually with overwritten id)"""
        return Problem(id or self.id, self.title, self.description,
                       tuple(self.public_tests), tuple(self.hidden_tests),
                       self.source_name, self.author,
                       tuple(self.community_tests))


    def to_json(self) -> dict:
        return {'__weldon_Problem__': {
            field: getattr(self, field)
            for field in self.fields
        }}

    @staticmethod
    def from_json(data:dict) -> object:
        payload = data.get('__weldon_Problem__')
        if payload:
            return Problem(**payload)
