"""Problem class definition.

"""

import os


class Problem:
    """Definition of a problem, notabily description and unit tests"""

    def __init__(self, id:int, title:str, description:str, public_tests:iter,
                 hidden_tests:iter, source_name:str=None, author:str=None,
                 community_tests:iter=()):
        self._id = int(id)
        self._title = str(title)
        self._description = str(description)
        self._public_tests = tuple(public_tests)
        self._hidden_tests = tuple(hidden_tests)
        self._community_tests = tuple(community_tests)
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
