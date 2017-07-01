
import ast
import dis
from io import StringIO
from functools import partial


def flags_of(code): return dis.pretty_flags(code)
def bytecode_of(code):
    dis_code_out = StringIO()
    dis.dis(code, file=dis_code_out)
    return dis_code_out.getvalue()

def functions_in(code) -> iter:
    """Yield all codes found in given code.

    They are functions, or objects, or patch of valid code.

    """
    for obj in code.co_consts:
        if type(obj).__name__ == 'code':
            yield obj

def search_in_ast(code, found:callable) -> None or True:
    """Apply given predicate to all code and code inside the code
    until one returns a truthy value. Then return this value.
    Or return None.

    """
    ret = found(code)
    if ret: return ret
    for elem in functions_in(code):
        ret = search_in_ast(elem, found)
        if ret: return ret


def pprint(code, default_formatter=repr, padding_field=0, colsep=' | '):
    BYTE_CODE_INDICATION = '\t\t(use bytecode_of function for more details)'
    SPECIAL_PRINT = {  # field: function to apply on value
        'co_flags': flags_of,
        'co_code': lambda x: repr(x) + BYTE_CODE_INDICATION,
        'co_lnotab': lambda x: repr(x) + BYTE_CODE_INDICATION,
        'co_lnotab': lambda x: repr(x) + BYTE_CODE_INDICATION,
    }
    fields = {attr: getattr(code, attr) for attr in dir(code)
              if attr.startswith('co_')}
    printables = {
        field: SPECIAL_PRINT.get(field, default_formatter)(value) or value
        for field, value in fields.items()
    }
    field_width = len(max(fields, key=len)) + padding_field
    for field, value in printables.items():
        yield field.rjust(field_width) + colsep + str(value)


def introspect_test_function(source_code:str, *,
                             only_one_function:bool=True,
                             name_starts_with:str or [str]='test_',
                             no_parameter_allowed=True,
                             must_have_one_of=(['AssertionError'], ('pytest', 'raises')),
                             prohibited_modules=('shutil', 'importlib'),
                             prohibited_builtins=('globals', 'locals'),
                            )-> ValueError or None:
    """Raise ValueError if anything in given test source code do not match
    expectations, that are modulable by the other parameters.

    """
    must_have_one_of = tuple(must_have_one_of)
    try:
        fast = ast.parse(source_code)
        compiled = compile(fast, '', 'exec')
    except (IndentationError, SyntaxError) as e:
        raise ValueError("Function compilation went bad because of {} at line {}."
                         "".format(e.msg, e.lineno))
    callables_in_source = tuple(functions_in(compiled))
    if only_one_function:
        if len(callables_in_source) > 1:
            raise ValueError("Multiple callables found in given source code.")
        if len(callables_in_source) < 1:
            raise ValueError("No callable found in given source code.")

    for test_function in callables_in_source:

        if name_starts_with and not test_function.co_name.startswith(name_starts_with):
            raise ValueError("Function '{}' name do not start by {}."
                             "".format(test_function.co_name, name_starts_with))

        if no_parameter_allowed and test_function.co_argcount > 0:
            raise ValueError("Function '{}' must not expects ({}) parameters."
                             "".format(test_function.co_name, test_function.co_argcount))

        if must_have_one_of:
            wanted_keys = tuple(map(set, must_have_one_of))
            found_keys = (
                search_in_ast(test_function, lambda co: wanted_key <= set(co.co_names))
                for wanted_key in wanted_keys
            )
            if not any(found_keys):
                raise ValueError("Function '{}' must use/raise {}."
                                 "".format(test_function.co_name,
                                           ' or '.join(' & '.join(key) for key in must_have_one_of)))

        if prohibited_modules:  # ensure that none of them are imported
            prohibited_modules_set = set(prohibited_modules)
            if search_in_ast(test_function, lambda co: prohibited_modules_set & set(co.co_names)):
                raise ValueError("Function '{}' must not use modules {}."
                                 "".format(test_function.co_name,
                                           ', '.join(prohibited_modules)))

        if prohibited_builtins:  # ensure that none of them are used
            prohibited_builtins_set = set(prohibited_builtins)
            if search_in_ast(test_function, lambda co: prohibited_builtins_set & (set(co.co_names) | set(co.co_varnames))):
                raise ValueError("Function '{}' must not use builtins {}."
                                 "".format(test_function.co_name,
                                           ', '.join(prohibited_builtins)))
    # every tests succeed. The code seems ok to go.
    return


def __experimentation():
    func = """
    hadoken = 32

    def foo():
        def infoo():
            print("foo")
        infoo()
        infoo()

    for i in range(63):
        print(34)

    class Truc:
        pass

    def bar(a):
        return a + 1
    """
    func = """
    @hadoken
    def test_foo():
        a = 2
        a = b
        assert a == 2
        def infoo():
            with pytest.raises(ValueError):
                # import importlib
                print("foo", a)
            print("foo", a)
        infoo()
    """
    print(dis.code_info(func))
    # Create the AST instance for it
    fast = ast.parse(func)
    compiled = compile(fast, '', 'exec')

    print('#' * 80 + '\t\tCOMPILED CODE')
    print('\n'.join(pprint(compiled)))
    print('FUNCTIONS:', tuple(functions_in(compiled)))
    print('#' * 80, end='\n\n\n')


    for obj in compiled.co_consts:
        if type(obj).__name__ == 'code':
            print('OBJECT', obj, type(obj), 'FunctionDef' if isinstance(obj, ast.FunctionDef) else '')
            print('#' * 80)
            print('\n'.join(pprint(obj)))
            print('#' * 80, end='\n\n')
        else:
            print('OBJECT:', obj, type(obj), 'FunctionDef' if isinstance(obj, ast.FunctionDef) else '')


