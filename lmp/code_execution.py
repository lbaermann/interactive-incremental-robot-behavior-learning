from dataclasses import dataclass
from types import NoneType, FunctionType
from typing import Any, Dict

import numpy as np

from .namespace import DynamicNamespaceDict
from .util import print_code

_MAX_DYNAMIC_EXECUTION_RECURSION_DEPTH = 10


@dataclass
class _ExecutionResult:
    return_value: Any
    defined_local_vars: Dict[str, Any]


class CodeExecutionEnvironment:

    def __init__(self,
                 namespace: DynamicNamespaceDict) -> None:
        """
        Create a new code executor.
        """
        super().__init__()
        self.namespace = namespace
        self.recursion_counter = 0

    def is_defined(self, name):
        # noinspection PyBroadException
        try:
            self.namespace[name]
        except:
            return name in __builtins__  # Builtins are always available
        else:
            return True

    def del_dynamic_value(self, name: str):
        del self.namespace[name]

    def __call__(self, code, local_vars_output_dict=None, return_val_name=None, define=False):
        if local_vars_output_dict is None:
            local_vars_output_dict = {}
        result = self._exec_safe_with_recursion_check(code)
        local_vars_output_dict.update(result.defined_local_vars)
        if return_val_name:
            value = local_vars_output_dict[return_val_name]
            if define:
                self.namespace[return_val_name] = value
            return value

    def _exec_safe_with_recursion_check(self, code: str, eval_mode=False) -> _ExecutionResult:
        self.recursion_counter += 1
        if self.recursion_counter > _MAX_DYNAMIC_EXECUTION_RECURSION_DEPTH:
            raise RecursionError(code)
        try:
            return _exec_safe(code, self.namespace.build_globals_dict(), eval_mode)
        except RecursionError as e:
            raise RecursionError(code, *e.args)  # To keep the dynamic code trace
        finally:
            self.recursion_counter -= 1


def _exec_safe(code_str, global_vars=None, eval_mode=False) -> _ExecutionResult:
    banned_phrases = ['import', '__']
    for phrase in banned_phrases:
        if phrase in code_str:
            raise ImportError(code_str)

    if global_vars is None:
        global_vars = {}
    global_vars = _deep_copy_except_complex_types(global_vars)
    global_vars.update(exec=_empty_fn, eval=_empty_fn, compile=_empty_fn)
    # noinspection PyTypeChecker
    global_vars['__builtins__'] = dict(__builtins__)
    global_vars['__builtins__'].update(exec=_empty_fn, eval=_empty_fn, open=_empty_fn,
                                       compile=_empty_fn, input=_empty_fn, exit=_empty_fn)
    global_vars['__builtins__']['__import__'] = None

    # The parameter "locals" for exec/eval is set to none because it has a weird semantic.
    #   see https://docs.python.org/3.10/library/functions.html#exec
    # Instead, everything is written into globals and then extracted from there.
    all_keys_before = set(global_vars.keys())
    primitive_globals_before = {k: v for k, v in global_vars.items() if _is_primitive_value(v)}
    # to properly detect in-place modifications of containers, do a deep copy before
    primitive_globals_before = _deep_copy_except_complex_types(primitive_globals_before)
    function_defs_before = {k: v for k, v in global_vars.items() if isinstance(v, FunctionType)}
    if eval_mode:
        print('\n\n', '=' * 30, '\n\n')
        print('eval', code_str)
        return_value = eval(code_str, global_vars, None)
    else:
        print('\n\n', '=' * 30, '\n\n')
        print_code(code_str)
        exec(code_str, global_vars, None)
        return_value = None

    # Keep variables that appeared newly or changed
    # New values can be anything including functions (to allow dynamic function definitions)
    # Functions are tracked so that self-defined functions can be redefined.
    primitive_globals_after = {k: v for k, v in global_vars.items()
                               if _is_primitive_value(v) and k in primitive_globals_before}
    changed_keys = {k for k in primitive_globals_before.keys()
                    if not _save_equals(primitive_globals_after.get(k), primitive_globals_before[k])
                    } | {k for k in function_defs_before.keys() if global_vars[k] != function_defs_before[k]}
    new_keys = global_vars.keys() - all_keys_before
    local_vars = {}
    for k in new_keys | changed_keys:
        local_vars[k] = global_vars[k]
    print('Updated/Defined variables after execution:', local_vars)

    return _ExecutionResult(return_value, local_vars)


def _save_equals(x, y):
    t1 = type(x)
    t2 = type(y)
    if t1 != t2:
        return False
    if t1 in [int, float, str, bool, NoneType]:
        return x == y
    elif t1 in [list, tuple, set]:
        return (len(x) == len(y)
                and all(_save_equals(a, b) for a, b in zip(x, y)))
    elif t1 == dict:
        return len(x) == len(y) and all(k in y and _save_equals(x[k], y[k]) for k in x.keys())
    elif t1 == np.ndarray:
        return (x.shape == y.shape
                and np.equal(x, y).all())
    elif np.isscalar(x):
        return np.equal(x, y)
    else:
        raise TypeError(x)


def _is_primitive_value(x):
    if type(x) in [int, float, str, bool, NoneType, np.ndarray]:
        return True
    elif np.isscalar(x):
        return True
    elif type(x) in [list, tuple, set]:
        return all(_is_primitive_value(y) for y in x)
    elif type(x) == dict:
        return all(_is_primitive_value(k) and _is_primitive_value(v) for k, v in x.items())
    else:
        return False


def _deep_copy_except_complex_types(x):
    if type(x) in [int, float, str, bool, NoneType]:
        return x
    if np.isscalar(x):
        return x
    elif type(x) in [list, tuple, set]:
        return type(x)(_deep_copy_except_complex_types(y) for y in x)
    elif type(x) == dict:
        return {_deep_copy_except_complex_types(k): _deep_copy_except_complex_types(v) for k, v in x.items()}
    else:
        return x


def _empty_fn(*args, **kwargs):
    pass
