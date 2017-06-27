"""Definition of the Test class.

"""


class Test:
    """A Test instance is a unit test ready to be launched.
    It should be associated with a Problem.

    """

    def __init__(self, source_code:str, author:str):
        self.source_code = str(source_code).strip('\n') + '\n'
        self.author = str(author)

    def __str__(self):
        """Return the ready to be print in file version of the instance"""
        return str(self.source_code)

    @staticmethod
    def to_test_suite(tests:[str or Test], author:str='unknow') -> (Test,):
        return tuple(test if isinstance(test, Test) else Test(test, author)
                     for test in tests)
