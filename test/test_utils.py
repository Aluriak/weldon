
from commons import jsonable_class


def test_jsonable_class():
    TestResult = jsonable_class('TestResult', ('_name, _type, _succeed'))
    tr = TestResult('testname',  'community', True)
    reloaded = TestResult.from_json(tr.to_json())
    assert tr.to_json() == {'__weldon_TestResult__': {
        'name': 'testname', 'type': 'community', 'succeed': True}}
    assert tr != reloaded
    for obj in (tr, reloaded):
        assert obj.name == obj._name
        assert obj.name == 'testname'
        assert obj.type == obj._type
        assert obj.type == 'community'
        assert obj.succeed == obj._succeed
        assert obj.succeed == True


def test_2_simultaneous_jsonable_class():
    """Detects namespace clashes"""
    One = jsonable_class('One', ('_name, _type, _succeed'))
    Two = jsonable_class('Two', ('_fame, _fype, _fucceed'))
    one = One(1, 2, 3)
    two = Two(4, 5, 6)
    assert repr(one) == '<One name=1 type=2 succeed=3>'
    assert repr(one) == str(one)
    assert repr(two) == '<Two fame=4 fype=5 fucceed=6>'
    assert repr(two) == str(two)
    assert one.name == 1
    assert one.type == 2
    assert one.succeed == 3
    assert two.fame == 4
    assert two.fype == 5
    assert two.fucceed == 6
    assert one.to_json() == {'__weldon_One__': {'name': 1, 'type': 2, 'succeed': 3}}
    assert two.to_json() == {'__weldon_Two__': {'fame': 4, 'fype': 5, 'fucceed': 6}}
