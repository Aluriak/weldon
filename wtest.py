"""Definition of the Test class.

"""

from ast_analysis import introspect_test_function
from commons import SourceError


VALID_TEST_TYPES = {'public', 'hidden', 'community'}


class Test:
    """A Test instance is a unit test ready to be launched.
    It should be associated with a Problem.

    """
    __slots__ = ['source_code', 'author', 'type', 'name']
    VALID_TEST_TYPES = VALID_TEST_TYPES
    SourceError = SourceError

    def __init__(self, source_code:str, author:str, type:str, name:str=''):
        self.source_code = str(source_code).strip('\n') + '\n'
        self.author = str(author)
        self.type = str(type)
        assert self.type in VALID_TEST_TYPES
        self.name = str(name)
        if not name:
            self.validate()

    def validate(self) -> None or SourceError:
        """Introspection of the function. Raise ValueError if anything wrong."""
        self.name = introspect_test_function(self.source_code, only_one_function=True)[0]

    def __str__(self):
        """Return the ready to be print in file version of the instance"""
        return str(self.source_code)

    @staticmethod
    def to_test_suite(tests:[str or 'Test'], author:str='unknow', type:str='public') -> ('Test',):
        return tuple(test if isinstance(test, Test) else Test(test, author, type)
                     for test in tests)


    @property
    def fields(self) -> iter:
        yield from (field.lstrip('_') for field in self.__slots__)


    def to_json(self) -> dict:
        return {'__weldon_Test__': {
            field: getattr(self, field)
            for field in self.fields
        }}

    @staticmethod
    def from_json(data:dict) -> object:
        payload = data.get('__weldon_Test__')
        if payload:
            return Test(**payload)
