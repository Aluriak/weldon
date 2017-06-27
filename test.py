"""Definition of the Test class.

"""


class Test:
    """A Test instance is a unit test ready to be launched.
    It should be associated with a Problem.

    """
    __slots__ = ['source_code', 'author']

    def __init__(self, source_code:str, author:str):
        self.source_code = str(source_code).strip('\n') + '\n'
        self.author = str(author)

    def __str__(self):
        """Return the ready to be print in file version of the instance"""
        return str(self.source_code)

    @staticmethod
    def to_test_suite(tests:[str or 'Test'], author:str='unknow') -> ('Test',):
        return tuple(test if isinstance(test, Test) else Test(test, author)
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
