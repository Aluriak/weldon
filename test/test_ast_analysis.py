
import textwrap
import pytest
from ast_analysis import introspect_test_function
from commons import SourceError


def test_ok():
    funcs = tuple(map(textwrap.dedent, ("""
    def test_foo():
        assert True
    ""","""
    @hadoken
    def test_foo():
        assert False
    ""","""
    def test_foo():
        def infoo():
            with pytest.raises(ValueError):
                pass
    """
    )))
    for func in funcs:
        assert introspect_test_function(func) == ('test_foo',)


def test_bad_name():
    func = textwrap.dedent("""
    def foo():
        assert True
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func, name_starts_with='hello')
    assert exc.exconly() == "commons.SourceError: Function 'foo' name do not start by hello."


def test_have_assert():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            assert False
    """)
    assert introspect_test_function(func) == ('test_foo',)


def test_have_pytest_raises():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            with pytest.raises(ValueError):
                pass
    """)
    assert introspect_test_function(func) == ('test_foo',)


def test_have_not_pytest_raises():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            pytest
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func)
    assert exc.exconly() == "commons.SourceError: Function 'test_foo' must use/raise AssertionError or pytest & raises."


def test_have_no_assert_or_pytest_raises():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            pass
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func, must_have_one_of=({'AssertionError'},))
    assert exc.exconly() == "commons.SourceError: Function 'test_foo' must use/raise AssertionError."


def test_prohibited_modules():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            with pytest.raises(ValueError):
                import importlib
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func, prohibited_modules=('importlib',))
    assert exc.exconly() == "commons.SourceError: Function 'test_foo' must not use modules importlib."


def test_prohibited_builtins():
    func = textwrap.dedent("""
    def test_foo():
        def infoo():
            globals()
        assert False
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func, prohibited_builtins=('globals',))
    assert exc.exconly() == "commons.SourceError: Function 'test_foo' must not use builtins globals."


def test_compilation_error_indent_1():
    func = textwrap.dedent("""
    def test_foo():
        pass
            pass
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func)
    assert exc.exconly() == "commons.SourceError: Function compilation went bad because of unexpected indent at line 4."


def test_compilation_error_indent_2():
    func = textwrap.dedent("""
    def test_foo():
            pass
        pass
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func)
    assert exc.exconly() == "commons.SourceError: Function compilation went bad because of unindent does not match any outer indentation level at line 4."


def test_compilation_error_syntax():
    func = textwrap.dedent("""
    def test_foo():
        a 2
    """)
    with pytest.raises(SourceError) as exc:
        introspect_test_function(func)
    assert exc.exconly() == "commons.SourceError: Function compilation went bad because of invalid syntax at line 3."
